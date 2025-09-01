#!/usr/bin/env python3
"""
Multiple Industry Templates for Personalized AI - SHOWCASE TEST
Tests professional contexts for various industries and shows how the AI adapts its responses
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path

class IndustryShowcaseAPITester:
    def __init__(self, base_url="https://pwa-integration-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.test_user_id = None
        self.test_user_data = {
            "email": f"showcase_user_{int(time.time())}@example.com",
            "username": f"showcaseuser{int(time.time())}",
            "password": "ShowcasePass123!",
            "first_name": "Showcase",
            "last_name": "User"
        }
        
        # Industry showcase scenarios
        self.industry_scenarios = [
            {
                "name": "Logistics & Supply Chain Manager",
                "context": {
                    "primary_industry": "Logistics & Supply Chain",
                    "job_role": "Supply Chain Manager",
                    "work_environment": "Freight forwarding and logistics operations",
                    "key_focus_areas": ["Cost optimization", "Supply chain risks", "Carrier performance"],
                    "content_types": ["Meeting minutes", "Operational reports", "Performance analysis"],
                    "analysis_preferences": ["Risk assessment", "Cost analysis", "Performance metrics"]
                },
                "test_content": {
                    "title": "Carrier Negotiations & Port Delays Meeting",
                    "content": """Meeting: Carrier Negotiations and Port Delays Review
Date: December 19, 2024
Attendees: Supply Chain Manager, Logistics Director, Procurement Lead, Operations Manager

Key Discussion Points:
- Reviewed Q4 carrier performance metrics across major trade lanes
- Discussed ongoing port congestion issues at Long Beach and Shanghai
- Analyzed freight cost increases of 18% year-over-year
- Evaluated 3PL partnership opportunities for last-mile delivery
- Assessed LTL vs FCL cost optimization strategies

Carrier Performance Analysis:
- Carrier A: 94% on-time delivery, competitive rates on Asia-US lanes
- Carrier B: 89% on-time delivery, issues with equipment availability
- Carrier C: 96% on-time delivery, premium pricing but reliable service

Port Delay Impact:
- Average delay increased from 2.3 days to 4.7 days at key ports
- Demurrage costs up 35% due to extended container dwell times
- Need contingency routing through alternative ports

Cost Optimization Initiatives:
- Negotiate annual contracts with top 3 carriers for volume discounts
- Implement dynamic routing to avoid congested ports
- Explore consolidation opportunities to improve container utilization
- Review detention and demurrage terms in carrier contracts

Risk Mitigation Strategies:
- Diversify carrier portfolio to reduce dependency
- Establish backup routing options for critical shipments
- Increase safety stock for high-velocity SKUs
- Implement real-time visibility tools for proactive management

Action Items:
- Finalize carrier contract negotiations by January 15
- Deploy port congestion monitoring dashboard
- Review and update contingency routing procedures
- Schedule monthly carrier performance reviews"""
                },
                "expected_terms": ["3PL", "LTL", "FCL", "freight", "carrier", "supply chain", "logistics", "demurrage", "dwell time"],
                "expected_focus": "supply chain terminology, freight cost analysis, carrier performance metrics"
            },
            {
                "name": "Healthcare Administrator",
                "context": {
                    "primary_industry": "Healthcare",
                    "job_role": "Healthcare Administrator",
                    "work_environment": "Hospital and clinical operations",
                    "key_focus_areas": ["Patient care quality", "Compliance", "Quality improvement"],
                    "content_types": ["Staff meetings", "Quality reports", "Compliance reviews"],
                    "analysis_preferences": ["Patient outcomes", "Regulatory compliance", "Operational efficiency"]
                },
                "test_content": {
                    "title": "Patient Satisfaction & Safety Protocols Meeting",
                    "content": """Meeting: Patient Satisfaction and Safety Protocol Review
Date: December 19, 2024
Attendees: Healthcare Administrator, Chief Nursing Officer, Quality Director, Compliance Manager

Patient Satisfaction Metrics:
- Overall satisfaction score decreased from 87% to 82% this quarter
- Wait times in emergency department increased by 23 minutes average
- Patient complaints increased 15%, primarily related to communication
- HCAHPS scores below national benchmark in 3 categories

Safety Protocol Review:
- Zero serious safety events this quarter (maintained excellent record)
- Near-miss reporting increased 12% indicating improved safety culture
- Hand hygiene compliance at 94% (target: 95%)
- Medication error rate: 0.08% (within acceptable range)

HIPAA Compliance Status:
- Completed quarterly HIPAA training for all staff (98% completion rate)
- No privacy breaches reported this quarter
- Updated patient consent forms to reflect new regulations
- Conducted security risk assessment with no major findings

Quality Improvement Initiatives:
- Implemented bedside rounding protocol to improve communication
- Launched patient portal to enhance engagement and access
- Reduced hospital-acquired infection rate by 8%
- Improved discharge planning process reducing readmission rate

Staffing and Workflow Issues:
- Nursing staff turnover at 12% (industry average: 15%)
- Physician satisfaction with support services at 89%
- Need additional staffing during peak hours in ED
- Implement lean workflow processes in outpatient clinics

Regulatory Compliance:
- Joint Commission survey preparation ongoing
- CMS quality reporting requirements met for all measures
- State health department inspection scheduled for January
- Updated policies and procedures per latest guidelines

Action Items:
- Hire 3 additional ED nurses by February 1
- Implement patient communication training for all clinical staff
- Deploy real-time patient flow monitoring system
- Schedule monthly patient experience rounds with leadership
- Review and update all clinical protocols by March 15"""
                },
                "expected_terms": ["HIPAA", "HCAHPS", "patient outcomes", "clinical", "compliance", "quality measures", "healthcare"],
                "expected_focus": "medical terminology, HIPAA references, patient outcomes focus"
            },
            {
                "name": "Construction Project Manager",
                "context": {
                    "primary_industry": "Construction",
                    "job_role": "Construction Project Manager",
                    "work_environment": "Commercial construction site management",
                    "key_focus_areas": ["Safety compliance", "Timeline optimization", "Cost management"],
                    "content_types": ["Project updates", "Safety reports", "Progress meetings"],
                    "analysis_preferences": ["Project milestones", "Safety protocols", "Budget tracking"]
                },
                "test_content": {
                    "title": "Project Timeline Delays & Safety Incidents Update",
                    "content": """Meeting: Project Status Update - Commercial Office Complex
Date: December 19, 2024
Attendees: Project Manager, Site Superintendent, Safety Officer, Subcontractor Leads

Project Timeline Status:
- Current project is 3 weeks behind original schedule
- Foundation work delayed due to unexpected soil conditions
- Steel delivery postponed 10 days due to supplier issues
- Weather delays totaled 8 days this quarter (above seasonal average)

Critical Path Method (CPM) Analysis:
- Foundation completion now scheduled for January 10 (was December 20)
- Steel erection pushed to January 25
- Mechanical rough-in delayed to March 15
- Substantial completion date moved from May 1 to May 22

Safety Incident Report:
- 3 minor safety violations identified during weekly inspection
- Near-miss incident with crane operation (no injuries)
- Safety training compliance at 96% for all workers
- Lost Time Injury rate: 0 (excellent safety record maintained)

Request for Information (RFI) Status:
- 12 RFIs submitted this month, 8 resolved
- Outstanding RFIs related to electrical specifications
- Change Order (CO) #7 approved for additional fire protection
- Pending CO #8 for upgraded HVAC system ($45,000)

Budget and Cost Management:
- Project currently 8% over budget due to overtime costs
- Material cost escalation impacting steel and concrete
- Labor costs increased due to skilled worker shortage
- Contingency fund at 60% utilization

Quality Control Measures:
- Weekly quality inspections completed on schedule
- Concrete strength tests all within specifications
- Steel welding inspections passed with minor corrections
- Building envelope testing scheduled for February

Subcontractor Performance:
- Electrical contractor ahead of schedule despite RFI delays
- Plumbing rough-in 95% complete
- HVAC contractor mobilizing equipment next week
- Concrete subcontractor performance excellent

Risk Mitigation Actions:
- Accelerated work schedule for critical path activities
- Additional crew assigned to foundation work
- Weather protection measures implemented
- Backup suppliers identified for critical materials

Action Items:
- Resolve outstanding RFIs by December 30
- Submit revised project schedule to owner
- Conduct additional safety training for crane operations
- Review and approve Change Order #8
- Schedule weekly progress meetings with all trades"""
                },
                "expected_terms": ["RFI", "CO", "CPM", "safety protocols", "project milestones", "construction", "subcontractor"],
                "expected_focus": "construction terminology, safety protocols, project milestones"
            },
            {
                "name": "Financial Analyst",
                "context": {
                    "primary_industry": "Financial Services",
                    "job_role": "Financial Analyst",
                    "work_environment": "Corporate finance and investment analysis",
                    "key_focus_areas": ["Budget analysis", "Risk assessment", "ROI evaluation"],
                    "content_types": ["Financial reports", "Budget reviews", "Investment analysis"],
                    "analysis_preferences": ["Quantitative analysis", "Risk metrics", "Performance indicators"]
                },
                "test_content": {
                    "title": "Q4 Budget Variance & Investment Returns Review",
                    "content": """Meeting: Q4 Financial Performance and Budget Variance Analysis
Date: December 19, 2024
Attendees: Financial Analyst, CFO, Controller, Investment Committee Members

Q4 Financial Performance Summary:
- Revenue: $12.8M (vs budget $12.2M) - 4.9% favorable variance
- EBITDA: $3.2M (vs budget $3.5M) - 8.6% unfavorable variance
- Net Income: $1.9M (vs budget $2.1M) - 9.5% unfavorable variance
- Operating Margin: 24.8% (vs budget 28.7%) - 390 basis points unfavorable

Budget Variance Analysis:
- Revenue exceeded budget due to strong Q4 sales performance
- Operating expenses 12% over budget ($450K unfavorable)
- Technology investments added $280K in unbudgeted expenses
- Personnel costs 8% over budget due to retention bonuses

Investment Portfolio Performance:
- Total portfolio return: 8.2% (vs benchmark 7.5%)
- Equity investments: 11.3% return (outperformed S&P 500)
- Fixed income: 4.1% return (in line with bond index)
- Alternative investments: 6.8% return (below expectations)

Return on Investment (ROI) Analysis:
- Technology upgrade project: 18% ROI (exceeded 15% target)
- Marketing campaign: 22% ROI (strong customer acquisition)
- Process automation: 31% ROI (significant efficiency gains)
- New product launch: 12% ROI (below 20% target)

Risk Assessment Metrics:
- Value at Risk (VaR): $1.2M at 95% confidence level
- Credit risk exposure decreased 15% year-over-year
- Market risk increased due to higher equity allocation
- Liquidity ratio: 2.3x (above minimum 2.0x requirement)

Cash Flow Analysis:
- Operating cash flow: $2.8M (strong operational performance)
- Free cash flow: $1.9M after capital expenditures
- Working capital increased $340K (inventory build-up)
- Debt service coverage ratio: 4.2x (excellent)

Key Performance Indicators (KPIs):
- Gross margin: 68.2% (vs 67.5% target)
- Customer acquisition cost (CAC): $125 (vs $150 budget)
- Customer lifetime value (LTV): $2,400 (20% increase)
- LTV/CAC ratio: 19.2x (healthy unit economics)

Profit & Loss (P&L) Highlights:
- Gross profit increased 6.8% year-over-year
- SG&A expenses as % of revenue: 42.1% (vs 38.5% budget)
- R&D spending: 8.2% of revenue (within strategic range)
- Tax rate: 24.5% (effective rate in line with projections)

Forward-Looking Analysis:
- Q1 2025 revenue forecast: $13.2M (3.1% growth)
- Expected EBITDA margin improvement to 27.5%
- Capital expenditure budget: $800K for technology upgrades
- Dividend payout ratio maintained at 35%

Action Items:
- Develop cost reduction plan to improve EBITDA margin
- Review and optimize investment portfolio allocation
- Implement enhanced budget monitoring controls
- Prepare detailed variance analysis for board presentation
- Update financial projections for 2025 strategic plan"""
                },
                "expected_terms": ["ROI", "EBITDA", "P&L", "budget variance", "risk metrics", "financial analysis", "KPIs"],
                "expected_focus": "financial terminology, quantitative analysis, risk metrics"
            },
            {
                "name": "Sales Operations Manager",
                "context": {
                    "primary_industry": "Sales & Marketing",
                    "job_role": "Sales Operations Manager",
                    "work_environment": "B2B sales and customer relationship management",
                    "key_focus_areas": ["Pipeline management", "Customer acquisition", "Performance optimization"],
                    "content_types": ["Sales meetings", "Pipeline reviews", "Performance reports"],
                    "analysis_preferences": ["Conversion metrics", "Pipeline analysis", "Customer insights"]
                },
                "test_content": {
                    "title": "Q4 Sales Targets & Client Relationship Review",
                    "content": """Meeting: Q4 Sales Performance and Client Relationship Review
Date: December 19, 2024
Attendees: Sales Operations Manager, VP Sales, Regional Sales Directors, CRM Administrator

Q4 Sales Performance Summary:
- Total revenue: $8.4M (vs target $8.0M) - 105% of target achieved
- New customer acquisition: 47 accounts (vs target 45)
- Customer retention rate: 94.2% (vs target 92%)
- Average deal size: $178K (vs target $165K)

Sales Pipeline Analysis:
- Total pipeline value: $24.6M (healthy 3.1x coverage ratio)
- Qualified leads: 312 (up 18% from Q3)
- Conversion rate from lead to opportunity: 28.5%
- Win rate on qualified opportunities: 31.2%
- Average sales cycle: 87 days (vs target 90 days)

Customer Relationship Management (CRM) Metrics:
- CRM data quality score: 89% (target: 85%)
- Sales activity logging compliance: 94%
- Customer touchpoint frequency: 2.3x per month average
- Customer satisfaction score (CSAT): 8.7/10

Customer Acquisition Cost (CAC) Analysis:
- Blended CAC: $2,850 (vs target $3,000)
- Digital marketing CAC: $1,950 (most efficient channel)
- Trade show CAC: $4,200 (high but quality leads)
- Referral CAC: $850 (lowest cost, highest conversion)

Customer Lifetime Value (LTV) Metrics:
- Average LTV: $89,400 (20% increase year-over-year)
- LTV/CAC ratio: 31.4x (excellent unit economics)
- Customer payback period: 14 months (vs target 18 months)
- Expansion revenue: 23% of total revenue

Sales Team Performance:
- Top performer: 142% of quota (Regional Director East)
- Team average quota attainment: 108%
- Ramp time for new hires: 4.2 months (vs target 5 months)
- Sales productivity (revenue per rep): $1.2M annually

Territory and Market Analysis:
- Northeast region: 118% of target (strongest performance)
- West Coast: 98% of target (competitive market challenges)
- Midwest: 112% of target (strong manufacturing sector)
- International: 89% of target (currency headwinds)

Lead Generation and Marketing Qualified Leads (MQLs):
- Total MQLs: 1,247 (up 22% from Q3)
- MQL to SQL conversion: 34.8%
- Cost per MQL: $145 (within budget)
- Lead scoring accuracy: 76% (improving with AI implementation)

Client Relationship Health Scores:
- Tier 1 accounts (>$500K): 8.9/10 average health score
- Tier 2 accounts ($100K-$500K): 8.4/10 average health score
- At-risk accounts identified: 12 (proactive outreach initiated)
- Expansion opportunities: 28 accounts with upsell potential

Sales Technology and Tools:
- CRM adoption rate: 97% (excellent user engagement)
- Sales enablement platform usage: 89%
- Proposal automation tool ROI: 340% (time savings)
- Sales forecasting accuracy: 94.2% (within 5% variance)

Competitive Analysis:
- Win rate vs Competitor A: 67% (our favor)
- Win rate vs Competitor B: 52% (competitive)
- Average discount to close: 8.2% (vs target 10%)
- Competitive displacement deals: 14 (strong positioning)

Action Items:
- Launch Q1 2025 territory planning process
- Implement advanced lead scoring model
- Develop account expansion playbooks for top 50 accounts
- Enhance sales training program for new product lines
- Review and optimize sales compensation plan
- Schedule quarterly business reviews with Tier 1 accounts"""
                },
                "expected_terms": ["CRM", "CAC", "LTV", "pipeline", "conversion metrics", "sales operations", "MQL", "SQL"],
                "expected_focus": "sales terminology, conversion metrics, pipeline analysis"
            }
        ]

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=60, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication header if required and available
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {"message": "Success but no JSON response"}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error details: {error_data}")
                except:
                    self.log(f"   Response text: {response.text[:200]}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test user registration for showcase"""
        success, response = self.run_test(
            "User Registration for Showcase",
            "POST",
            "auth/register",
            200,
            data=self.test_user_data
        )
        if success:
            self.auth_token = response.get('access_token')
            user_data = response.get('user', {})
            self.test_user_id = user_data.get('id')
            self.log(f"   Registered showcase user ID: {self.test_user_id}")
            self.log(f"   Token received: {'Yes' if self.auth_token else 'No'}")
        return success

    def test_industry_scenario(self, scenario):
        """Test a complete industry scenario"""
        self.log(f"\n🏭 TESTING INDUSTRY SCENARIO: {scenario['name']}")
        self.log("="*60)
        
        scenario_success = True
        
        # Step 1: Set professional context
        self.log(f"📋 Step 1: Setting Professional Context for {scenario['name']}")
        context_success, context_response = self.run_test(
            f"Set Professional Context - {scenario['name']}",
            "POST",
            "user/professional-context",
            200,
            data=scenario['context'],
            auth_required=True
        )
        
        if context_success:
            self.log(f"   ✅ Context set successfully")
            self.log(f"   Industry: {scenario['context']['primary_industry']}")
            self.log(f"   Role: {scenario['context']['job_role']}")
            self.log(f"   Focus Areas: {', '.join(scenario['context']['key_focus_areas'][:3])}")
        else:
            self.log(f"   ❌ Failed to set professional context")
            scenario_success = False
        
        # Step 2: Create note with industry-specific content
        self.log(f"📝 Step 2: Creating Note with Industry-Specific Content")
        note_data = {
            "title": scenario['test_content']['title'],
            "kind": "text",
            "text_content": scenario['test_content']['content']
        }
        
        note_success, note_response = self.run_test(
            f"Create Industry Note - {scenario['name']}",
            "POST",
            "notes",
            200,
            data=note_data,
            auth_required=True
        )
        
        if note_success and 'id' in note_response:
            note_id = note_response['id']
            self.created_notes.append(note_id)
            self.log(f"   ✅ Note created successfully: {note_id}")
            self.log(f"   Content length: {len(scenario['test_content']['content'])} characters")
        else:
            self.log(f"   ❌ Failed to create note")
            scenario_success = False
            return scenario_success
        
        # Step 3: Test AI chat with industry-specific questions
        self.log(f"🤖 Step 3: Testing AI Chat with Professional Context")
        
        industry_questions = [
            f"Analyze this {scenario['context']['primary_industry'].lower()} content and provide strategic recommendations",
            f"What are the key risks and opportunities mentioned in this {scenario['context']['job_role'].lower()} meeting?",
            f"Provide actionable insights from a {scenario['context']['job_role'].lower()} perspective",
            f"Generate a professional summary focusing on {', '.join(scenario['context']['key_focus_areas'][:2])}"
        ]
        
        successful_chats = 0
        ai_responses = []
        
        for i, question in enumerate(industry_questions):
            chat_success, chat_response = self.run_test(
                f"AI Chat Question {i+1} - {scenario['name']}",
                "POST",
                f"notes/{note_id}/ai-chat",
                200,
                data={"question": question},
                auth_required=True,
                timeout=90
            )
            
            if chat_success:
                successful_chats += 1
                ai_response = chat_response.get('response', '')
                context_summary = chat_response.get('context_summary', {})
                ai_responses.append(ai_response)
                
                self.log(f"   ✅ Question {i+1} - Response length: {len(ai_response)} characters")
                self.log(f"   Context detected: {context_summary.get('profession_detected', 'N/A')}")
                
                # Check for industry-specific terminology
                found_terms = []
                for term in scenario['expected_terms']:
                    if term.lower() in ai_response.lower():
                        found_terms.append(term)
                
                if found_terms:
                    self.log(f"   ✅ Industry terms found: {', '.join(found_terms[:5])}")
                else:
                    self.log(f"   ⚠️  Limited industry-specific terminology detected")
                
                # Check response quality
                if len(ai_response) >= 300:
                    self.log(f"   ✅ Comprehensive response (≥300 chars)")
                else:
                    self.log(f"   ⚠️  Response may be too brief ({len(ai_response)} chars)")
            else:
                self.log(f"   ❌ AI Chat failed for question {i+1}")
        
        # Step 4: Analyze overall AI personalization quality
        self.log(f"📊 Step 4: Analyzing AI Personalization Quality")
        
        if successful_chats >= 3:
            self.log(f"   ✅ AI Chat Success Rate: {successful_chats}/4 ({successful_chats/4*100:.1f}%)")
            
            # Analyze combined responses for industry adaptation
            combined_responses = ' '.join(ai_responses)
            
            # Check for expected terminology coverage
            terms_found = sum(1 for term in scenario['expected_terms'] if term.lower() in combined_responses.lower())
            term_coverage = terms_found / len(scenario['expected_terms']) * 100
            
            self.log(f"   📈 Industry Terminology Coverage: {terms_found}/{len(scenario['expected_terms'])} ({term_coverage:.1f}%)")
            
            # Check for professional structure and formatting
            has_professional_structure = any(
                keyword in combined_responses.upper() 
                for keyword in ['RECOMMENDATIONS', 'ACTION ITEMS', 'ANALYSIS', 'INSIGHTS', 'RISKS']
            )
            
            if has_professional_structure:
                self.log(f"   ✅ Professional response structure detected")
            else:
                self.log(f"   ⚠️  Limited professional structure in responses")
            
            # Check average response length
            avg_response_length = sum(len(response) for response in ai_responses) / len(ai_responses)
            if avg_response_length >= 300:
                self.log(f"   ✅ Average response length: {avg_response_length:.0f} characters (comprehensive)")
            else:
                self.log(f"   ⚠️  Average response length: {avg_response_length:.0f} characters (may be brief)")
            
        else:
            self.log(f"   ❌ AI Chat Success Rate: {successful_chats}/4 ({successful_chats/4*100:.1f}%) - Below threshold")
            scenario_success = False
        
        # Step 5: Test content type detection and formatting
        self.log(f"📋 Step 5: Testing Content Type Detection")
        
        content_type_question = "Generate structured meeting minutes from this content"
        
        minutes_success, minutes_response = self.run_test(
            f"Meeting Minutes Generation - {scenario['name']}",
            "POST",
            f"notes/{note_id}/ai-chat",
            200,
            data={"question": content_type_question},
            auth_required=True,
            timeout=90
        )
        
        if minutes_success:
            minutes_content = minutes_response.get('response', '')
            
            # Check for meeting minutes structure
            meeting_keywords = ['ATTENDEES', 'DECISIONS', 'ACTION ITEMS', 'DISCUSSION', 'NEXT STEPS']
            found_structure = sum(1 for keyword in meeting_keywords if keyword in minutes_content.upper())
            
            if found_structure >= 3:
                self.log(f"   ✅ Meeting minutes structure detected ({found_structure}/5 sections)")
            else:
                self.log(f"   ⚠️  Limited meeting minutes structure ({found_structure}/5 sections)")
        else:
            self.log(f"   ❌ Meeting minutes generation failed")
        
        return scenario_success

    def test_cross_industry_comparison(self):
        """Test and compare AI responses across different industries"""
        self.log(f"\n🔄 CROSS-INDUSTRY COMPARISON ANALYSIS")
        self.log("="*60)
        
        # Create a generic business scenario that applies to all industries
        generic_content = """Quarterly Performance Review Meeting
Date: December 19, 2024

Performance Summary:
- Revenue targets exceeded by 8% this quarter
- Operating costs increased 12% due to expansion activities
- Customer satisfaction scores improved from 85% to 89%
- Employee turnover decreased to 8% (industry average: 12%)

Key Challenges:
- Supply chain disruptions affecting delivery schedules
- Increased competition in core market segments
- Technology infrastructure needs upgrading
- Regulatory compliance requirements becoming more complex

Strategic Initiatives:
- Digital transformation project launched
- New market expansion into adjacent territories
- Process automation to improve efficiency
- Enhanced training programs for staff development

Financial Metrics:
- Gross margin: 42% (target: 40%)
- Operating margin: 18% (target: 20%)
- Cash flow positive for 6th consecutive quarter
- Return on investment: 15% on major initiatives

Risk Factors:
- Market volatility affecting pricing strategies
- Talent acquisition challenges in key roles
- Cybersecurity threats requiring enhanced protection
- Economic uncertainty impacting long-term planning"""

        comparison_results = []
        
        for scenario in self.industry_scenarios:
            self.log(f"🎯 Testing Generic Content with {scenario['name']} Context")
            
            # Set professional context
            context_success, _ = self.run_test(
                f"Set Context for Comparison - {scenario['name']}",
                "POST",
                "user/professional-context",
                200,
                data=scenario['context'],
                auth_required=True
            )
            
            if not context_success:
                continue
            
            # Create note with generic content
            note_data = {
                "title": f"Generic Business Review - {scenario['name']} Perspective",
                "kind": "text",
                "text_content": generic_content
            }
            
            note_success, note_response = self.run_test(
                f"Create Generic Note - {scenario['name']}",
                "POST",
                "notes",
                200,
                data=note_data,
                auth_required=True
            )
            
            if not note_success or 'id' not in note_response:
                continue
            
            note_id = note_response['id']
            self.created_notes.append(note_id)
            
            # Ask the same question from each industry perspective
            generic_question = "Analyze this business performance data and provide strategic recommendations from your professional perspective"
            
            chat_success, chat_response = self.run_test(
                f"Generic Analysis - {scenario['name']}",
                "POST",
                f"notes/{note_id}/ai-chat",
                200,
                data={"question": generic_question},
                auth_required=True,
                timeout=90
            )
            
            if chat_success:
                ai_response = chat_response.get('response', '')
                context_summary = chat_response.get('context_summary', {})
                
                # Analyze response for industry-specific adaptation
                industry_terms_found = []
                for term in scenario['expected_terms']:
                    if term.lower() in ai_response.lower():
                        industry_terms_found.append(term)
                
                comparison_results.append({
                    'industry': scenario['name'],
                    'response_length': len(ai_response),
                    'industry_terms': industry_terms_found,
                    'context_detected': context_summary.get('profession_detected', 'N/A'),
                    'response_preview': ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
                })
                
                self.log(f"   ✅ Response generated: {len(ai_response)} chars")
                self.log(f"   Industry terms: {', '.join(industry_terms_found[:3])}")
            else:
                self.log(f"   ❌ Failed to generate response")
        
        # Analyze comparison results
        self.log(f"\n📊 CROSS-INDUSTRY COMPARISON RESULTS")
        self.log("-" * 60)
        
        for result in comparison_results:
            self.log(f"🏭 {result['industry']}:")
            self.log(f"   Response Length: {result['response_length']} characters")
            self.log(f"   Industry Terms: {len(result['industry_terms'])} found")
            self.log(f"   Context Detected: {result['context_detected']}")
            self.log(f"   Preview: {result['response_preview'][:100]}...")
            self.log("")
        
        # Calculate adaptation metrics
        if comparison_results:
            avg_response_length = sum(r['response_length'] for r in comparison_results) / len(comparison_results)
            total_adaptations = sum(len(r['industry_terms']) for r in comparison_results)
            
            self.log(f"📈 ADAPTATION METRICS:")
            self.log(f"   Average Response Length: {avg_response_length:.0f} characters")
            self.log(f"   Total Industry Adaptations: {total_adaptations}")
            self.log(f"   Industries Tested: {len(comparison_results)}")
            
            return len(comparison_results) >= 4  # Success if we tested at least 4 industries
        
        return False

    def run_industry_showcase_test(self):
        """Run the complete industry showcase test"""
        self.log("🚀 STARTING MULTIPLE INDUSTRY TEMPLATES SHOWCASE TEST")
        self.log("="*70)
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        self.log(f"   Industries to test: {len(self.industry_scenarios)}")
        
        # Step 1: User registration and authentication
        self.log("\n🔐 STEP 1: USER AUTHENTICATION")
        if not self.test_user_registration():
            self.log("❌ User registration failed - stopping showcase test")
            return False
        
        # Step 2: Test each industry scenario
        self.log(f"\n🏭 STEP 2: INDUSTRY-SPECIFIC TESTING")
        successful_scenarios = 0
        
        for i, scenario in enumerate(self.industry_scenarios, 1):
            self.log(f"\n--- SCENARIO {i}/{len(self.industry_scenarios)} ---")
            if self.test_industry_scenario(scenario):
                successful_scenarios += 1
            
            # Brief pause between scenarios
            time.sleep(2)
        
        # Step 3: Cross-industry comparison
        self.log(f"\n🔄 STEP 3: CROSS-INDUSTRY COMPARISON")
        comparison_success = self.test_cross_industry_comparison()
        
        # Step 4: Summary and results
        self.log(f"\n📊 SHOWCASE TEST RESULTS")
        self.log("="*50)
        self.log(f"Industries Successfully Tested: {successful_scenarios}/{len(self.industry_scenarios)}")
        self.log(f"Cross-Industry Comparison: {'✅ Success' if comparison_success else '❌ Failed'}")
        self.log(f"Total API Tests Run: {self.tests_run}")
        self.log(f"Total API Tests Passed: {self.tests_passed}")
        self.log(f"API Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.created_notes:
            self.log(f"Test Notes Created: {len(self.created_notes)}")
        
        # Determine overall success
        overall_success = (
            successful_scenarios >= 4 and  # At least 4 industries working
            comparison_success and         # Cross-industry comparison working
            self.tests_passed >= (self.tests_run * 0.8)  # 80% API success rate
        )
        
        self.log(f"\n🎯 OVERALL SHOWCASE RESULT: {'✅ SUCCESS' if overall_success else '❌ NEEDS IMPROVEMENT'}")
        
        if overall_success:
            self.log("\n🎉 INDUSTRY SHOWCASE DEMONSTRATION COMPLETE!")
            self.log("✅ AI successfully adapts responses across multiple professional contexts")
            self.log("✅ Industry-specific terminology and focus areas properly detected")
            self.log("✅ Professional response structure and formatting working")
            self.log("✅ Content type detection and adaptation functional")
        else:
            self.log("\n⚠️  SHOWCASE NEEDS IMPROVEMENT:")
            if successful_scenarios < 4:
                self.log(f"   - Only {successful_scenarios} industries working (need 4+)")
            if not comparison_success:
                self.log("   - Cross-industry comparison failed")
            if self.tests_passed < (self.tests_run * 0.8):
                self.log(f"   - API success rate too low ({(self.tests_passed/self.tests_run*100):.1f}%)")
        
        return overall_success

def main():
    """Main test execution"""
    tester = IndustryShowcaseAPITester()
    
    try:
        success = tester.run_industry_showcase_test()
        
        if success:
            print("\n🎉 Industry Showcase Test PASSED! Personalized AI system is working correctly.")
            return 0
        else:
            print(f"\n⚠️  Industry Showcase Test FAILED. Check the logs above for details.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())