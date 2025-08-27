import logging
from typing import Dict, Any, Optional, List
import re

logger = logging.getLogger(__name__)

class AIContextProcessor:
    """Dynamic AI context generation based on user profession and content type"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Profession-based context templates
        self.profession_contexts = {
            # Logistics & Supply Chain
            'logistics': {
                'keywords': ['logistics', 'supply chain', 'freight', 'cargo', 'shipping', 'distribution', 'warehouse'],
                'analysis_focus': [
                    'Cost optimization opportunities',
                    'Supply chain risks and mitigation strategies',
                    'Operational efficiency improvements',
                    'Vendor/carrier performance analysis',
                    'Inventory management insights',
                    'Transportation mode recommendations',
                    'Cross-border compliance considerations'
                ],
                'terminology': 'logistics terminology (FOB, CIF, LCL, FCL, etc.)',
                'metrics': ['cost per shipment', 'transit times', 'delivery reliability', 'inventory turnover'],
                'stakeholders': ['suppliers', 'carriers', 'customs', 'customers', 'distribution centers']
            },
            
            # Construction & Trades
            'construction': {
                'keywords': ['construction', 'building', 'contractor', 'site', 'materials', 'safety', 'project'],
                'analysis_focus': [
                    'Project timeline and milestone analysis',
                    'Safety risk assessment and compliance',
                    'Material cost optimization',
                    'Labor productivity insights',
                    'Quality control recommendations',
                    'Regulatory compliance requirements',
                    'Equipment utilization efficiency'
                ],
                'terminology': 'construction terminology (BOQ, RFI, CO, etc.)',
                'metrics': ['project progress', 'cost per square meter', 'safety incidents', 'material waste'],
                'stakeholders': ['architects', 'engineers', 'contractors', 'inspectors', 'clients']
            },
            
            # Automotive (Panel Beater, Mechanic)
            'automotive': {
                'keywords': ['automotive', 'panel', 'paint', 'repair', 'vehicle', 'insurance', 'customer'],
                'analysis_focus': [
                    'Repair process efficiency analysis',
                    'Cost estimation accuracy',
                    'Quality control standards',
                    'Customer satisfaction insights',
                    'Insurance claim processing',
                    'Workflow optimization opportunities',
                    'Equipment maintenance recommendations'
                ],
                'terminology': 'automotive repair terminology',
                'metrics': ['repair time', 'cost per job', 'customer satisfaction', 'rework rates'],
                'stakeholders': ['customers', 'insurance companies', 'parts suppliers', 'inspectors']
            },
            
            # Sales & CRM
            'sales': {
                'keywords': ['sales', 'customer', 'client', 'deal', 'pipeline', 'revenue', 'target'],
                'analysis_focus': [
                    'Sales pipeline analysis and forecasting',
                    'Customer relationship insights',
                    'Revenue optimization opportunities',
                    'Market trends and competitive analysis',
                    'Sales process improvement recommendations',
                    'Customer retention strategies',
                    'Territory performance analysis'
                ],
                'terminology': 'sales and CRM terminology',
                'metrics': ['conversion rates', 'average deal size', 'sales cycle length', 'customer lifetime value'],
                'stakeholders': ['prospects', 'customers', 'partners', 'sales team', 'management']
            },
            
            # Healthcare
            'healthcare': {
                'keywords': ['patient', 'medical', 'healthcare', 'clinical', 'treatment', 'diagnosis'],
                'analysis_focus': [
                    'Patient care quality improvements',
                    'Clinical workflow optimization',
                    'Compliance and regulatory considerations',
                    'Resource allocation efficiency',
                    'Patient satisfaction insights',
                    'Risk management recommendations',
                    'Technology integration opportunities'
                ],
                'terminology': 'medical terminology',
                'metrics': ['patient outcomes', 'treatment times', 'satisfaction scores', 'readmission rates'],
                'stakeholders': ['patients', 'medical staff', 'administrators', 'regulators']
            },
            
            # Manufacturing
            'manufacturing': {
                'keywords': ['production', 'manufacturing', 'quality', 'assembly', 'factory', 'equipment'],
                'analysis_focus': [
                    'Production efficiency optimization',
                    'Quality control improvements',
                    'Equipment maintenance strategies',
                    'Waste reduction opportunities',
                    'Safety protocol enhancements',
                    'Supply chain coordination',
                    'Cost reduction initiatives'
                ],
                'terminology': 'manufacturing terminology (OEE, lean, six sigma, etc.)',
                'metrics': ['production yield', 'defect rates', 'equipment uptime', 'cost per unit'],
                'stakeholders': ['operators', 'supervisors', 'quality team', 'maintenance', 'suppliers']
            },
            
            # Finance & Banking
            'finance': {
                'keywords': ['finance', 'banking', 'investment', 'accounting', 'budget', 'revenue', 'profit'],
                'analysis_focus': [
                    'Financial performance analysis',
                    'Risk assessment and mitigation',
                    'Budget optimization opportunities',
                    'Cash flow management insights',
                    'Compliance and regulatory requirements',
                    'Investment return analysis',
                    'Cost-benefit evaluations'
                ],
                'terminology': 'financial terminology (ROI, EBITDA, P&L, etc.)',
                'metrics': ['ROI', 'profit margins', 'cash flow', 'budget variance', 'risk ratios'],
                'stakeholders': ['investors', 'auditors', 'regulators', 'management', 'clients']
            },
            
            # Sales & Marketing
            'sales': {
                'keywords': ['sales', 'marketing', 'customer', 'lead', 'pipeline', 'conversion', 'campaign'],
                'analysis_focus': [
                    'Sales pipeline optimization',
                    'Customer acquisition strategies',
                    'Conversion rate improvements',
                    'Lead qualification insights',
                    'Market opportunity analysis',
                    'Customer retention strategies',
                    'Revenue growth initiatives'
                ],
                'terminology': 'sales terminology (CRM, CAC, LTV, etc.)',
                'metrics': ['conversion rates', 'sales velocity', 'pipeline value', 'customer lifetime value'],
                'stakeholders': ['prospects', 'customers', 'marketing team', 'management', 'partners']
            },
            
            # Technology & Software
            'technology': {
                'keywords': ['software', 'development', 'system', 'application', 'database', 'security', 'IT'],
                'analysis_focus': [
                    'System performance optimization',
                    'Security vulnerability assessment',
                    'Technical debt reduction',
                    'Scalability improvements',
                    'User experience enhancements',
                    'Integration opportunities',
                    'Development process optimization'
                ],
                'terminology': 'technical terminology (API, DevOps, CI/CD, etc.)',
                'metrics': ['system uptime', 'response times', 'error rates', 'user adoption'],
                'stakeholders': ['developers', 'users', 'IT teams', 'security teams', 'management']
            }
        }
        
        # Content type detection patterns
        self.content_types = {
            'meeting_minutes': {
                'patterns': ['meeting', 'discussed', 'agenda', 'attendees', 'action items', 'decisions'],
                'structure': 'formal meeting minutes format'
            },
            'crm_notes': {
                'patterns': ['customer', 'client call', 'follow up', 'proposal', 'quote', 'lead'],
                'structure': 'CRM activity log format'
            },
            'project_update': {
                'patterns': ['project', 'milestone', 'progress', 'timeline', 'deliverable', 'status'],
                'structure': 'project status report format'
            },
            'incident_report': {
                'patterns': ['incident', 'issue', 'problem', 'fault', 'error', 'failure'],
                'structure': 'incident analysis format'
            },
            'daily_standup': {
                'patterns': ['yesterday', 'today', 'tomorrow', 'blockers', 'completed', 'working on'],
                'structure': 'daily standup summary format'
            },
            'training_session': {
                'patterns': ['training', 'learning', 'course', 'workshop', 'skill', 'knowledge'],
                'structure': 'training summary format'
            },
            'performance_review': {
                'patterns': ['review', 'performance', 'goals', 'achievements', 'feedback', 'evaluation'],
                'structure': 'performance evaluation format'
            },
            'audit_report': {
                'patterns': ['audit', 'compliance', 'inspection', 'verification', 'standards', 'requirements'],
                'structure': 'audit findings format'
            },
            'financial_report': {
                'patterns': ['budget', 'expenses', 'revenue', 'profit', 'financial', 'cost'],
                'structure': 'financial analysis format'
            },
            'strategic_planning': {
                'patterns': ['strategy', 'planning', 'objectives', 'goals', 'vision', 'roadmap'],
                'structure': 'strategic plan format'
            }
        }
    
    def detect_profession_context(self, user_profile: Dict[str, Any]) -> str:
        """Detect user's profession context from profile"""
        profession = user_profile.get('profession', '').lower()
        industry = user_profile.get('industry', '').lower()
        interests = user_profile.get('interests', '').lower()
        
        combined_text = f"{profession} {industry} {interests}".lower()
        
        # Check for direct matches or keyword matches
        for prof_key, prof_data in self.profession_contexts.items():
            if prof_key in combined_text:
                return prof_key
            
            # Check for keyword matches
            keyword_matches = sum(1 for keyword in prof_data['keywords'] if keyword in combined_text)
            if keyword_matches >= 2:  # At least 2 keyword matches
                return prof_key
        
        # Default to generic business context
        return 'business'
    
    def detect_content_type(self, content: str) -> str:
        """Detect the type of content being analyzed"""
        content_lower = content.lower()
        
        for content_type, type_data in self.content_types.items():
            pattern_matches = sum(1 for pattern in type_data['patterns'] if pattern in content_lower)
            if pattern_matches >= 2:  # At least 2 pattern matches
                return content_type
        
        return 'general'
    
    def generate_dynamic_prompt(self, 
                              content: str, 
                              user_profile: Dict[str, Any], 
                              analysis_type: str = 'general') -> str:
        """Generate dynamic AI prompt based on enhanced user professional context"""
        
        # Get professional context fields
        primary_industry = user_profile.get('primary_industry', user_profile.get('industry', 'Business'))
        job_role = user_profile.get('job_role', user_profile.get('profession', 'Professional'))
        work_environment = user_profile.get('work_environment', '')
        key_focus_areas = user_profile.get('key_focus_areas', [])
        content_types = user_profile.get('content_types', [])
        analysis_preferences = user_profile.get('analysis_preferences', [])
        
        # Auto-detect content type and profession context
        profession_key = self.detect_profession_context(user_profile)
        detected_content_type = self.detect_content_type(content)
        
        # Get profession context template
        profession_context = self.profession_contexts.get(profession_key, self.profession_contexts.get('business', {}))
        
        # Build personalized prompt
        user_name = user_profile.get('first_name', 'Professional')
        
        prompt = f"""
You are an expert AI assistant specialized in {primary_industry} working with {user_name}, a {job_role}.

PROFESSIONAL CONTEXT:
- Industry: {primary_industry}
- Role: {job_role}
- Work Environment: {work_environment or 'Professional setting'}
- Key Focus Areas: {', '.join(key_focus_areas) if key_focus_areas else 'General business operations'}
- Content Types: {', '.join(content_types) if content_types else 'Mixed business content'}
- Analysis Style: {', '.join(analysis_preferences) if analysis_preferences else 'Comprehensive analysis'}

CONTENT TO ANALYZE:
{content}

ANALYSIS TYPE: {detected_content_type.replace('_', ' ').title()}
        """
        
        # Add profession-specific analysis focus
        if profession_context:
            prompt += f"""

INDUSTRY-SPECIFIC ANALYSIS FOCUS:
{primary_industry} priorities to consider:"""
            for focus_area in profession_context.get('analysis_focus', [])[:5]:  # Top 5 priorities
                prompt += f"\n• {focus_area}"
            
            # Add relevant metrics
            if profession_context.get('metrics'):
                prompt += f"""

KEY METRICS to reference: {', '.join(profession_context['metrics'])}"""
            
            # Add stakeholder context
            if profession_context.get('stakeholders'):
                prompt += f"""

STAKEHOLDER IMPACT to consider: {', '.join(profession_context['stakeholders'])}"""
        
        # Content type specific instructions
        if analysis_type == 'meeting_minutes' or 'meeting' in detected_content_type:
            prompt += f"""

MEETING MINUTES FORMAT:
Structure your response as professional meeting minutes with:
• ATTENDEES (infer from content)
• KEY DISCUSSIONS (main topics covered with {primary_industry} context)
• DECISIONS MADE (specific to {job_role} responsibilities)
• ACTION ITEMS (with {primary_industry}-specific priorities and owners)
• NEXT STEPS (relevant to {primary_industry} workflows)
"""
        elif detected_content_type == 'crm_notes':
            prompt += f"""

CRM ANALYSIS FORMAT:
Provide a comprehensive client interaction summary with:
• CLIENT PROFILE (key details and context)
• DISCUSSION SUMMARY ({primary_industry}-specific insights)
• OPPORTUNITIES IDENTIFIED (relevant to {job_role} goals)
• FOLLOW-UP ACTIONS (specific and time-bound)
• RELATIONSHIP STATUS (progression and next steps)
"""
        elif detected_content_type == 'project_update':
            prompt += f"""

PROJECT STATUS FORMAT:
Analyze as a {primary_industry} project with:
• PROJECT OVERVIEW (current status and {primary_industry} context)
• PROGRESS ANALYSIS (against {job_role} objectives)
• RISK ASSESSMENT ({primary_industry}-specific risks and mitigation)
• RESOURCE REQUIREMENTS (team, budget, timeline)
• RECOMMENDATIONS (actionable next steps for {job_role})
"""
        else:
            prompt += f"""

PROFESSIONAL ANALYSIS:
Provide {primary_industry}-focused insights that are:
• Actionable for a {job_role}
• Relevant to {primary_industry} operations
• Aligned with the specified analysis preferences: {', '.join(analysis_preferences) if analysis_preferences else 'comprehensive business analysis'}
• Focused on these key areas: {', '.join(key_focus_areas) if key_focus_areas else 'general business improvement'}
"""

        prompt += f"""

RESPONSE GUIDELINES:
- Use {primary_industry} terminology and best practices
- Be specific and actionable for a {job_role}
- Provide insights that drive real business value
- Format professionally for {work_environment or 'professional'} environment
- Keep response comprehensive but focused (aim for 300-500 words)
"""
        
        return prompt.strip()
        
        elif analysis_type == 'insights':
            prompt += f"""
            
            Provide {profession}-specific insights including:
            • KEY INSIGHTS (relevant to {industry})
            • OPPORTUNITIES (for {profession} improvement)
            • RISKS & CHALLENGES (industry-specific)
            • RECOMMENDED ACTIONS (actionable for a {profession})
            """
        
        elif analysis_type == 'summary':
            prompt += f"""
            
            Create a {profession}-focused summary highlighting:
            • EXECUTIVE OVERVIEW (for {industry} leadership)
            • CRITICAL POINTS (important for {profession} role)
            • IMPACT ASSESSMENT (on {industry} operations)
            • FOLLOW-UP PRIORITIES (for {profession})
            """
        
        prompt += f"""
        
        Use professional {industry} language and terminology. Be specific and actionable.
        Avoid generic business advice - focus on {profession}-relevant insights.
        """
        
        return prompt.strip()
    
    def get_context_summary(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of the user's context for debugging/display"""
        profession_key = self.detect_profession_context(user_profile)
        profession_context = self.profession_contexts.get(profession_key, {})
        
        return {
            'profession_detected': profession_key,
            'user_profession': user_profile.get('profession', 'Not specified'),
            'user_industry': user_profile.get('industry', 'Not specified'),
            'focus_areas': profession_context.get('analysis_focus', [])[:3],
            'key_metrics': profession_context.get('metrics', []),
            'primary_stakeholders': profession_context.get('stakeholders', [])[:3]
        }

# Global instance
ai_context_processor = AIContextProcessor()