"""
IISB (Issues, Impact, Solutions, Benefits) Analysis Processor
For Expeditors sales teams to systematically analyze client supply chain challenges
"""

import os
import json
import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from providers import stt_transcribe

logger = logging.getLogger(__name__)

@dataclass
class IISBItem:
    issue: str
    impact: str
    solution: str
    benefit: str
    category: str
    priority: str
    financial_impact: Optional[str] = None
    timeline: Optional[str] = None

class IISBProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Supply chain issue categories and patterns
        self.issue_categories = {
            'visibility': {
                'keywords': ['visibility', 'tracking', 'transparency', 'blind spot', 'cannot see', 'no idea', 'unknown'],
                'typical_impacts': ['labor planning issues', 'demurrage costs', 'customer dissatisfaction', 'reactive operations'],
                'solutions': ['Real-time tracking system', 'Visibility platform', 'Alert notifications', 'Dashboard reporting'],
                'benefits': ['Proactive planning', 'Cost reduction', 'Improved service levels', 'Better resource allocation']
            },
            'inventory': {
                'keywords': ['inventory', 'stock', 'warehousing', 'storage', 'stockout', 'overstock'],
                'typical_impacts': ['carrying costs', 'stockouts', 'obsolescence', 'cash flow issues'],
                'solutions': ['Inventory optimization', 'Demand planning', 'JIT delivery', 'Vendor managed inventory'],
                'benefits': ['Reduced carrying costs', 'Improved cash flow', 'Better service levels', 'Lower obsolescence']
            },
            'transportation': {
                'keywords': ['transport', 'shipping', 'delivery', 'freight', 'routing', 'delays'],
                'typical_impacts': ['higher costs', 'service failures', 'customer complaints', 'lost sales'],
                'solutions': ['Route optimization', 'Carrier management', 'Multi-modal transport', 'Consolidation'],
                'benefits': ['Cost savings', 'Faster delivery', 'Improved reliability', 'Better service quality']
            },
            'compliance': {
                'keywords': ['compliance', 'customs', 'regulatory', 'documentation', 'permits', 'certificates'],
                'typical_impacts': ['delays', 'penalties', 'rejected shipments', 'audit findings'],
                'solutions': ['Compliance management', 'Automated documentation', 'Regulatory monitoring', 'Training programs'],
                'benefits': ['Reduced delays', 'Avoided penalties', 'Better compliance scores', 'Smoother operations']
            },
            'cost_control': {
                'keywords': ['cost', 'expensive', 'budget', 'overrun', 'invoice', 'billing'],
                'typical_impacts': ['budget overruns', 'margin erosion', 'unprofitability', 'competitive disadvantage'],
                'solutions': ['Cost analytics', 'Spend management', 'Carrier negotiation', 'Process optimization'],
                'benefits': ['Cost reduction', 'Better margins', 'Improved profitability', 'Competitive advantage']
            },
            'communication': {
                'keywords': ['communication', 'coordination', 'information', 'updates', 'notifications'],
                'typical_impacts': ['misalignment', 'inefficiency', 'errors', 'customer dissatisfaction'],
                'solutions': ['Communication platform', 'Automated notifications', 'Collaboration tools', 'Status updates'],
                'benefits': ['Better coordination', 'Reduced errors', 'Improved efficiency', 'Higher satisfaction']
            }
        }
        
        # Financial impact estimators
        self.financial_estimators = {
            'demurrage': {'range': '$500-2000/day', 'description': 'Container detention charges'},
            'labor_cost': {'range': '$20-50/hour', 'description': 'Additional labor costs'},
            'carrying_cost': {'range': '15-25%/year', 'description': 'Inventory carrying costs'},
            'freight_premium': {'range': '10-30%', 'description': 'Rush/premium freight costs'},
            'compliance_penalty': {'range': '$1000-50000', 'description': 'Regulatory penalties'},
            'stockout_cost': {'range': '5-15% of sales', 'description': 'Lost sales opportunity'}
        }
        
        # Solution templates
        self.solution_templates = {
            'technology': [
                'Real-time visibility platform',
                'Automated tracking and alerts',
                'Digital documentation system',
                'Analytics and reporting dashboard',
                'Mobile application access'
            ],
            'process': [
                'Process standardization',
                'Workflow optimization',
                'Performance monitoring',
                'Quality management system',
                'Continuous improvement plan'
            ],
            'service': [
                'Dedicated account management',
                'Expert consultation',
                'Training and support',
                '24/7 customer service',
                'Escalation procedures'
            ]
        }

    async def process_iisb_input(self, client_name: str, input_text: str, input_type: str = "text") -> Dict[str, Any]:
        """Process IISB input and generate structured analysis"""
        try:
            # Handle voice input if needed
            if input_type == "audio":
                # This would be implemented if audio file is provided
                raw_text = input_text  # For now, assume text is provided
            else:
                raw_text = input_text
            
            # Extract issues from input
            issues = self._extract_issues(raw_text)
            
            # Process each issue through IISB framework
            iisb_items = []
            for issue_text in issues:
                iisb_item = self._process_single_issue(issue_text, client_name)
                if iisb_item:
                    iisb_items.append(iisb_item)
            
            # Generate comprehensive analysis
            analysis = self._generate_comprehensive_analysis(client_name, iisb_items, raw_text)
            
            # Create presentation-ready output
            presentation_data = self._create_presentation_data(client_name, iisb_items, analysis)
            
            return {
                "client_name": client_name,
                "raw_input": raw_text,
                "issues_identified": len(iisb_items),
                "iisb_items": [self._iisb_item_to_dict(item) for item in iisb_items],
                "analysis": analysis,
                "presentation_data": presentation_data,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Error processing IISB input: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }
    
    def _extract_issues(self, text: str) -> List[str]:
        """Extract individual issues from input text"""
        # Split text into potential issues
        issue_indicators = [
            'issue:', 'problem:', 'challenge:', 'difficulty:',
            'customer have', 'client have', 'they have',
            'abc customer', 'the customer', 'currently'
        ]
        
        issues = []
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Ignore very short sentences
                # Check if sentence contains issue indicators
                is_issue = any(indicator.lower() in sentence.lower() for indicator in issue_indicators)
                if is_issue or len(issues) == 0:  # Include first sentence or sentences with indicators
                    issues.append(sentence)
        
        return issues if issues else [text]  # Return full text if no specific issues found
    
    def _process_single_issue(self, issue_text: str, client_name: str) -> Optional[IISBItem]:
        """Process a single issue through the IISB framework"""
        try:
            # Categorize the issue
            category = self._categorize_issue(issue_text)
            
            # Generate impact analysis
            impact = self._generate_impact(issue_text, category)
            
            # Suggest solutions
            solution = self._generate_solution(issue_text, category)
            
            # Quantify benefits
            benefit = self._generate_benefit(issue_text, category, client_name)
            
            # Assess priority
            priority = self._assess_priority(issue_text, category)
            
            # Estimate financial impact
            financial_impact = self._estimate_financial_impact(issue_text, category)
            
            # Estimate timeline
            timeline = self._estimate_timeline(category)
            
            return IISBItem(
                issue=self._clean_issue_text(issue_text),
                impact=impact,
                solution=solution,
                benefit=benefit,
                category=category,
                priority=priority,
                financial_impact=financial_impact,
                timeline=timeline
            )
            
        except Exception as e:
            self.logger.error(f"Error processing issue: {str(e)}")
            return None
    
    def _categorize_issue(self, issue_text: str) -> str:
        """Categorize the issue based on keywords"""
        issue_lower = issue_text.lower()
        
        category_scores = {}
        for category, data in self.issue_categories.items():
            score = sum(1 for keyword in data['keywords'] if keyword in issue_lower)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        else:
            return 'operational'  # Default category
    
    def _generate_impact(self, issue_text: str, category: str) -> str:
        """Generate impact description based on issue and category"""
        category_data = self.issue_categories.get(category, {})
        typical_impacts = category_data.get('typical_impacts', ['operational inefficiency'])
        
        # Customize impact based on specific issue content
        if 'visibility' in issue_text.lower():
            return f"Without proper visibility, {typical_impacts[0]} occurs, leading to reactive decision-making, increased costs, and poor customer service levels."
        elif 'container' in issue_text.lower() and 'labor' in issue_text.lower():
            return "Inability to plan labor resources effectively due to lack of shipment visibility leads to either overstaffing (increased costs) or understaffing (operational delays and potential demurrage charges)."
        elif 'delay' in issue_text.lower():
            return f"Delays create cascading effects including {', '.join(typical_impacts[:2])}, ultimately impacting customer satisfaction and profitability."
        else:
            return f"This issue directly results in {typical_impacts[0]}, which can cascade into {', '.join(typical_impacts[1:3]) if len(typical_impacts) > 1 else 'broader operational challenges'}."
    
    def _generate_solution(self, issue_text: str, category: str) -> str:
        """Generate solution recommendations"""
        category_data = self.issue_categories.get(category, {})
        solutions = category_data.get('solutions', ['Process optimization'])
        
        # Build comprehensive solution
        primary_solution = solutions[0] if solutions else 'Process improvement'
        
        if category == 'visibility':
            return f"Implement {primary_solution} with real-time tracking capabilities, automated notifications, and comprehensive dashboard reporting to provide end-to-end supply chain visibility."
        elif category == 'transportation':
            return f"Deploy {primary_solution} combined with carrier performance management and alternative routing strategies to ensure reliable, cost-effective transportation."
        else:
            return f"Implement {primary_solution} alongside {solutions[1] if len(solutions) > 1 else 'supporting processes'} to address the root cause and prevent recurrence."
    
    def _generate_benefit(self, issue_text: str, category: str, client_name: str) -> str:
        """Generate quantified benefits"""
        category_data = self.issue_categories.get(category, {})
        benefits = category_data.get('benefits', ['Improved efficiency'])
        
        # Quantify benefits where possible
        if 'demurrage' in issue_text.lower():
            return f"Eliminate demurrage charges (typically $500-2000/day per container), improve labor efficiency by 15-20%, and enhance customer satisfaction through proactive communication."
        elif 'inventory' in category:
            return f"Reduce inventory carrying costs by 10-15%, improve stock availability by 95%+, and free up working capital for {client_name}'s growth initiatives."
        elif 'cost' in issue_text.lower():
            return f"Achieve 8-12% reduction in total logistics costs, improve budget predictability, and gain competitive advantage through optimized supply chain operations."
        else:
            return f"Realize {', '.join(benefits[:2])}, leading to measurable improvements in operational efficiency and customer satisfaction for {client_name}."
    
    def _assess_priority(self, issue_text: str, category: str) -> str:
        """Assess issue priority level"""
        high_priority_keywords = ['urgent', 'critical', 'immediate', 'demurrage', 'penalty', 'compliance', 'customer complaint']
        medium_priority_keywords = ['cost', 'efficiency', 'delay', 'visibility']
        
        issue_lower = issue_text.lower()
        
        if any(keyword in issue_lower for keyword in high_priority_keywords):
            return 'High'
        elif any(keyword in issue_lower for keyword in medium_priority_keywords):
            return 'Medium'
        else:
            return 'Low'
    
    def _estimate_financial_impact(self, issue_text: str, category: str) -> str:
        """Estimate financial impact of the issue"""
        issue_lower = issue_text.lower()
        
        if 'demurrage' in issue_lower:
            return self.financial_estimators['demurrage']['range']
        elif 'labor' in issue_lower:
            return self.financial_estimators['labor_cost']['range']
        elif 'inventory' in issue_lower or 'stock' in issue_lower:
            return self.financial_estimators['carrying_cost']['range']
        elif 'freight' in issue_lower or 'transport' in issue_lower:
            return self.financial_estimators['freight_premium']['range']
        elif 'compliance' in issue_lower or 'penalty' in issue_lower:
            return self.financial_estimators['compliance_penalty']['range']
        else:
            return "TBD - Requires detailed assessment"
    
    def _estimate_timeline(self, category: str) -> str:
        """Estimate implementation timeline"""
        timeline_map = {
            'visibility': '4-6 weeks',
            'transportation': '2-4 weeks', 
            'inventory': '6-8 weeks',
            'compliance': '3-6 weeks',
            'cost_control': '4-8 weeks',
            'communication': '2-3 weeks'
        }
        
        return timeline_map.get(category, '4-6 weeks')
    
    def _clean_issue_text(self, issue_text: str) -> str:
        """Clean and format issue text"""
        # Remove common prefixes and clean up text
        cleaned = re.sub(r'^(issue:|problem:|challenge:)\s*', '', issue_text.strip(), flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        
        # Ensure proper capitalization
        if cleaned and not cleaned[0].isupper():
            cleaned = cleaned[0].upper() + cleaned[1:]
        
        return cleaned
    
    def _generate_comprehensive_analysis(self, client_name: str, iisb_items: List[IISBItem], raw_input: str) -> Dict[str, Any]:
        """Generate comprehensive analysis summary"""
        if not iisb_items:
            return {}
        
        # Categorize issues
        categories = {}
        priorities = {'High': 0, 'Medium': 0, 'Low': 0}
        
        for item in iisb_items:
            categories[item.category] = categories.get(item.category, 0) + 1
            priorities[item.priority] = priorities.get(item.priority, 0) + 1
        
        # Generate insights
        primary_category = max(categories, key=categories.get) if categories else 'operational'
        total_issues = len(iisb_items)
        
        return {
            'executive_summary': f"{client_name} faces {total_issues} key supply chain challenges, primarily in {primary_category} areas. {priorities['High']} high-priority issues require immediate attention.",
            'issue_breakdown': {
                'by_category': categories,
                'by_priority': priorities,
                'primary_focus': primary_category
            },
            'strategic_recommendations': [
                f"Address {priorities['High']} high-priority issues within next 30 days",
                f"Implement comprehensive {primary_category} improvements",
                "Establish performance monitoring and continuous improvement process",
                "Create implementation roadmap with clear milestones and success metrics"
            ],
            'expected_outcomes': [
                "Significant reduction in operational costs and inefficiencies",
                "Improved customer satisfaction and service levels", 
                "Enhanced supply chain visibility and control",
                "Stronger competitive position in the market"
            ],
            'next_steps': [
                "Schedule detailed assessment workshop with key stakeholders",
                "Develop customized solution proposal with timeline and pricing",
                "Conduct pilot program for highest priority issues",
                "Establish success metrics and monitoring framework"
            ]
        }
    
    def _create_presentation_data(self, client_name: str, iisb_items: List[IISBItem], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create presentation-ready data structure"""
        return {
            'client_name': client_name,
            'title': f"{client_name} - Supply Chain Analysis",
            'subtitle': "Issues, Impact, Solutions & Benefits Assessment",
            'summary_stats': {
                'total_issues': len(iisb_items),
                'high_priority': sum(1 for item in iisb_items if item.priority == 'High'),
                'categories_affected': len(set(item.category for item in iisb_items)),
                'estimated_savings': "15-25% logistics cost reduction potential"
            },
            'iisb_matrix': [
                {
                    'issue': item.issue,
                    'impact': item.impact,
                    'solution': item.solution,
                    'benefit': item.benefit,
                    'priority': item.priority,
                    'category': item.category.replace('_', ' ').title(),
                    'financial_impact': item.financial_impact,
                    'timeline': item.timeline
                }
                for item in iisb_items
            ],
            'analysis_summary': analysis,
            'presentation_settings': {
                'template': 'expeditors_iisb',
                'color_scheme': 'professional_blue_orange',
                'logo_placement': 'header_right',
                'confidentiality': 'Confidential - Client Presentation',
                'export_formats': ['pptx', 'pdf', 'web_interactive']
            }
        }
    
    def _iisb_item_to_dict(self, item: IISBItem) -> Dict[str, Any]:
        """Convert IISBItem to dictionary"""
        return {
            'issue': item.issue,
            'impact': item.impact,
            'solution': item.solution,
            'benefit': item.benefit,
            'category': item.category,
            'priority': item.priority,
            'financial_impact': item.financial_impact,
            'timeline': item.timeline
        }

# Global processor instance
iisb_processor = IISBProcessor()