import os
import json
import logging
from typing import Dict, List, Any, Optional
from providers import stt_transcribe, ocr_read
from storage import create_presigned_get_url
from expeditors_templates import template_engine

logger = logging.getLogger(__name__)

class NetworkDiagramProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Expeditors-specific locations and codes (expanded)
        self.expeditors_locations = {
            # Major Asian Airports
            'SHA': {'name': 'Shanghai Hongqiao', 'type': 'airport', 'region': 'Asia', 'country': 'China', 'coordinates': (31.1979, 121.3362)},
            'PVG': {'name': 'Shanghai Pudong', 'type': 'airport', 'region': 'Asia', 'country': 'China', 'coordinates': (31.1434, 121.8052)},
            'HKG': {'name': 'Hong Kong International', 'type': 'airport', 'region': 'Asia', 'country': 'Hong Kong', 'coordinates': (22.3080, 113.9185)},
            'NRT': {'name': 'Tokyo Narita', 'type': 'airport', 'region': 'Asia', 'country': 'Japan', 'coordinates': (35.7647, 140.3864)},
            'ICN': {'name': 'Seoul Incheon', 'type': 'airport', 'region': 'Asia', 'country': 'South Korea', 'coordinates': (37.4602, 126.4407)},
            'SIN': {'name': 'Singapore Changi', 'type': 'airport', 'region': 'Asia', 'country': 'Singapore', 'coordinates': (1.3644, 103.9915)},
            
            # African Airports
            'JNB': {'name': 'Johannesburg OR Tambo', 'type': 'airport', 'region': 'Africa', 'country': 'South Africa', 'coordinates': (-26.1367, 28.2411)},
            'ORT': {'name': 'OR Tambo International', 'type': 'airport', 'region': 'Africa', 'country': 'South Africa', 'coordinates': (-26.1367, 28.2411)},
            'CPT': {'name': 'Cape Town International', 'type': 'airport', 'region': 'Africa', 'country': 'South Africa', 'coordinates': (-33.9648, 18.6017)},
            'DUR': {'name': 'Durban King Shaka', 'type': 'airport', 'region': 'Africa', 'country': 'South Africa', 'coordinates': (-29.6144, 31.1197)},
            
            # European Airports  
            'FRA': {'name': 'Frankfurt Main', 'type': 'airport', 'region': 'Europe', 'country': 'Germany', 'coordinates': (50.0333, 8.5706)},
            'CDG': {'name': 'Paris Charles de Gaulle', 'type': 'airport', 'region': 'Europe', 'country': 'France', 'coordinates': (49.0097, 2.5479)},
            'LHR': {'name': 'London Heathrow', 'type': 'airport', 'region': 'Europe', 'country': 'United Kingdom', 'coordinates': (51.4700, -0.4543)},
            'AMS': {'name': 'Amsterdam Schiphol', 'type': 'airport', 'region': 'Europe', 'country': 'Netherlands', 'coordinates': (52.3086, 4.7639)},
            
            # Major Ports
            'CNSHA': {'name': 'Shanghai Port', 'type': 'port', 'region': 'Asia', 'country': 'China', 'coordinates': (31.2304, 121.4737)},
            'SGSIN': {'name': 'Singapore Port', 'type': 'port', 'region': 'Asia', 'country': 'Singapore', 'coordinates': (1.2966, 103.8518)},
            'NLRTM': {'name': 'Rotterdam Port', 'type': 'port', 'region': 'Europe', 'country': 'Netherlands', 'coordinates': (51.9225, 4.4792)},
            'ZADUR': {'name': 'Durban Port', 'type': 'port', 'region': 'Africa', 'country': 'South Africa', 'coordinates': (-29.8587, 31.0218)},
        }
        
        # Enhanced supply chain flow patterns  
        self.flow_patterns = {
            'airfreight': {
                'icon': '✈️',
                'color': '#3498DB',
                'typical_routes': ['SHA-JNB', 'HKG-JNB', 'FRA-JNB', 'CDG-JNB', 'SIN-JNB', 'NRT-JNB'],
                'characteristics': ['fast', 'high_value', 'time_sensitive'],
                'transit_time': '1-3 days'
            },
            'warehouse': {
                'icon': '🏭',
                'color': '#E67E22', 
                'operations': ['EI Transit WH', 'Distribution Center', 'Cross-dock', 'Consolidation Hub'],
                'characteristics': ['storage', 'sorting', 'consolidation'],
                'typical_dwell': '1-5 days'
            },
            'road_transport': {
                'icon': '🚛',
                'color': '#27AE60',
                'services': ['Local delivery', 'Cross-border', 'Last mile', 'Regional distribution'],
                'characteristics': ['flexible', 'door_to_door', 'cost_effective'],
                'transit_time': '1-7 days'
            },
            'ocean_freight': {
                'icon': '🚢',
                'color': '#1B4F72',
                'services': ['Container shipping', 'Bulk cargo', 'FCL', 'LCL'],
                'characteristics': ['high_volume', 'cost_effective', 'slow'],
                'transit_time': '14-45 days'
            },
            'customs': {
                'icon': '📋',
                'color': '#8E44AD',
                'processes': ['Clearance', 'Documentation', 'Inspection', 'Duty payment'],
                'characteristics': ['regulatory', 'documentation', 'compliance'],
                'typical_duration': '1-3 days'
            },
            'rail_freight': {
                'icon': '🚂',
                'color': '#9B59B6',
                'services': ['Container rail', 'Intermodal', 'Bulk rail'],
                'characteristics': ['medium_speed', 'eco_friendly', 'scheduled'],
                'transit_time': '5-15 days'
            }
        }
    
    async def process_network_input(self, file_url: str, input_type: str) -> Dict[str, Any]:
        """Process network diagram input (voice or sketch) with professional templates"""
        try:
            if input_type == "audio":
                result = await stt_transcribe(file_url)
                raw_text = result.get("text", "")
            elif input_type == "image":
                result = await ocr_read(file_url)
                raw_text = result.get("text", "")
            else:
                raise ValueError(f"Unsupported input type: {input_type}")
            
            # Extract supply chain entities with enhanced processing
            entities = self._extract_supply_chain_entities(raw_text)
            
            # Determine best template based on network characteristics
            template_name = self._select_optimal_template(entities)
            
            # Generate network topology with template guidance
            network_topology = self._generate_network_topology(entities, template_name)
            
            # Get professional template configuration
            template_config = template_engine.generate_network_config(template_name, {"network_topology": network_topology})
            
            # Create visual diagram data with PowerPoint styling
            diagram_data = self._create_professional_diagram_data(network_topology, template_config)
            
            # Generate enhanced insights and recommendations
            insights = self._generate_professional_insights(network_topology, entities)
            
            # Add PowerPoint export configuration
            powerpoint_config = self._generate_powerpoint_config(template_config, network_topology)
            
            return {
                "raw_input": raw_text,
                "entities": entities,
                "network_topology": network_topology,
                "diagram_data": diagram_data,
                "template_config": template_config,
                "powerpoint_config": powerpoint_config,
                "insights": insights,
                "professional_features": {
                    "expeditors_branding": True,
                    "template_applied": template_name,
                    "export_ready": True,
                    "presentation_quality": True
                },
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Error processing network input: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }
    
    def _select_optimal_template(self, entities: Dict[str, List[str]]) -> str:
        """Select the best template based on network characteristics"""
        
        # Analyze network structure
        airport_count = len(entities.get('airports', []))
        warehouse_count = len(entities.get('warehouses', []))
        transport_modes = len(entities.get('transport_modes', []))
        
        # Template selection logic
        if airport_count > 3 and warehouse_count == 1:
            return "hub_and_spoke"  # Multiple origins to single hub
        elif transport_modes > 2:
            return "multi_modal_transport"  # Multiple transport modes
        else:
            return "supply_chain_flow"  # Default linear flow
    
    def _create_professional_diagram_data(self, topology: Dict[str, Any], template_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create professional diagram data with PowerPoint styling"""
        return {
            'title': 'Expeditors Supply Chain Network Analysis',
            'subtitle': 'Professional Network Diagram',
            'nodes': topology['nodes'],
            'edges': topology['edges'],
            'template': template_config['template_name'],
            'styling': template_config['styling'],
            'layout': template_config['layout'],
            'animations': template_config['animations'],
            'branding': {
                'company': 'Expeditors International',
                'logo_position': 'top_right',
                'color_scheme': 'expeditors_professional',
                'footer_text': 'Global Supply Chain Solutions'
            },
            'export_formats': ['interactive_web', 'png_hd', 'svg_vector', 'powerpoint_ready'],
            'professional_features': {
                'smart_layout': True,
                'flow_animations': True,
                'hover_details': True,
                'zoom_navigation': True,
                'export_controls': True
            }
        }
    
    def _generate_powerpoint_config(self, template_config: Dict[str, Any], topology: Dict[str, Any]) -> Dict[str, Any]:
        """Generate PowerPoint-specific configuration"""
        return {
            'slide_dimensions': {'width': 1920, 'height': 1080},
            'template_style': template_config['template_name'],
            'color_palette': template_config['styling']['color_palette'],
            'node_positioning': 'auto_layout_optimized',
            'connection_styling': 'professional_arrows',
            'text_formatting': {
                'title_font': 'Segoe UI Bold',
                'body_font': 'Segoe UI',
                'sizes': {'title': 28, 'subtitle': 18, 'body': 14, 'caption': 12}
            },
            'slide_elements': {
                'header': {
                    'company_logo': True,
                    'title': True,
                    'date_generated': True
                },
                'main_diagram': {
                    'network_visualization': True,
                    'legend': True,
                    'flow_indicators': True
                },
                'footer': {
                    'company_name': 'Expeditors International',
                    'confidentiality': 'Confidential - Client Presentation',
                    'page_number': True
                }
            },
            'export_settings': {
                'resolution': '300dpi',
                'format': 'pptx',
                'compatibility': 'PowerPoint 2016+',
                'embedded_fonts': True
            }
        }
    
    def _generate_professional_insights(self, topology: Dict[str, Any], entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Generate professional-grade insights and recommendations"""
        nodes = topology['nodes']
        edges = topology['edges']
        
        insights = {
            'executive_summary': {
                'network_complexity': self._assess_network_complexity(nodes, edges),
                'primary_routes': self._identify_primary_routes(edges),
                'key_hubs': self._identify_key_hubs(nodes, edges),
                'transport_mix': self._analyze_transport_mix(entities)
            },
            'operational_analysis': {
                'capacity_utilization': self._estimate_capacity_utilization(nodes),
                'transit_time_analysis': self._analyze_transit_times(edges),
                'cost_optimization_potential': self._assess_cost_optimization(topology),
                'risk_factors': self._identify_risk_factors(nodes, edges)
            },
            'strategic_recommendations': [
                "Implement real-time visibility across all network nodes",
                "Consider backup routing options for critical lanes",
                "Evaluate consolidation opportunities at hub locations",
                "Optimize inventory positioning to reduce transit times"
            ],
            'kpi_metrics': {
                'network_coverage': len(set(node.get('region', '') for node in nodes)),
                'modal_diversity': len(set(edge.get('type', '') for edge in edges)),
                'hub_efficiency_score': self._calculate_hub_efficiency(nodes, edges),
                'route_optimization_index': self._calculate_route_optimization(edges)
            },
            'next_steps': [
                "Schedule detailed capacity planning session",
                "Initiate technology integration assessment", 
                "Develop service level agreement framework",
                "Create performance monitoring dashboard"
            ]
        }
        
        return insights
    
    def _assess_network_complexity(self, nodes: List[Dict], edges: List[Dict]) -> str:
        """Assess network complexity level"""
        total_connections = len(edges)
        total_nodes = len(nodes)
        
        if total_connections > 10 and total_nodes > 6:
            return "High - Complex multi-hub network requiring sophisticated management"
        elif total_connections > 5 and total_nodes > 3:
            return "Medium - Moderate complexity with multiple routing options"
        else:
            return "Low - Simple linear flow with minimal complexity"
    
    def _identify_primary_routes(self, edges: List[Dict]) -> List[str]:
        """Identify primary transportation routes"""
        route_types = {}
        for edge in edges:
            route_type = edge.get('type', 'unknown')
            route_types[route_type] = route_types.get(route_type, 0) + 1
        
        return [f"{route_type} ({count} connections)" for route_type, count in sorted(route_types.items(), key=lambda x: x[1], reverse=True)]
    
    def _identify_key_hubs(self, nodes: List[Dict], edges: List[Dict]) -> List[str]:
        """Identify key hub locations"""
        hub_connections = {}
        for edge in edges:
            source = edge.get('source', '')
            target = edge.get('target', '')
            hub_connections[source] = hub_connections.get(source, 0) + 1
            hub_connections[target] = hub_connections.get(target, 0) + 1
        
        # Find nodes with most connections
        key_hubs = sorted(hub_connections.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return [f"{hub} ({connections} connections)" for hub, connections in key_hubs]
    
    def _analyze_transport_mix(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Analyze transportation mode mix"""
        transport_modes = entities.get('transport_modes', [])
        
        return {
            'primary_modes': [mode.get('mode', 'unknown') for mode in transport_modes],
            'modal_balance': 'Balanced' if len(transport_modes) > 2 else 'Single-mode focused',
            'intermodal_potential': 'High' if len(transport_modes) > 1 else 'Limited'
        }
    
    def _estimate_capacity_utilization(self, nodes: List[Dict]) -> str:
        """Estimate capacity utilization across network"""
        hub_nodes = [node for node in nodes if node.get('type') == 'warehouse']
        
        if len(hub_nodes) > 2:
            return "Distributed - Good capacity distribution across multiple hubs"
        elif len(hub_nodes) == 1:
            return "Centralized - Single hub may face capacity constraints"
        else:
            return "Point-to-point - Direct connections without intermediate storage"
    
    def _analyze_transit_times(self, edges: List[Dict]) -> Dict[str, str]:
        """Analyze estimated transit times"""
        return {
            'average_transit': '3-5 days estimated',
            'critical_path': 'Origin to final destination',
            'optimization_opportunity': 'Consider express lanes for urgent shipments'
        }
    
    def _assess_cost_optimization(self, topology: Dict[str, Any]) -> List[str]:
        """Assess cost optimization opportunities"""
        return [
            "Consolidation at hub locations can reduce per-unit costs",
            "Multi-modal transport options may provide cost savings",
            "Direct routes vs. hub routing cost-benefit analysis recommended"
        ]
    
    def _identify_risk_factors(self, nodes: List[Dict], edges: List[Dict]) -> List[str]:
        """Identify potential risk factors"""
        risks = []
        
        # Single point of failure
        hub_count = len([node for node in nodes if node.get('type') == 'warehouse'])
        if hub_count == 1:
            risks.append("Single hub dependency creates potential bottleneck")
        
        # Geographic concentration
        regions = set(node.get('region', '') for node in nodes)
        if len(regions) < 2:
            risks.append("Limited geographic diversification")
        
        # Transport mode dependency
        transport_types = set(edge.get('type', '') for edge in edges)
        if len(transport_types) == 1:
            risks.append("Single transport mode creates service risk")
        
        return risks if risks else ["Low risk - Well-diversified network structure"]
    
    def _calculate_hub_efficiency(self, nodes: List[Dict], edges: List[Dict]) -> float:
        """Calculate hub efficiency score"""
        if not nodes or not edges:
            return 0.0
        
        # Simple efficiency calculation based on connection density
        connection_density = len(edges) / len(nodes) if nodes else 0
        return min(connection_density * 20, 100)  # Scale to 0-100
    
    def _calculate_route_optimization(self, edges: List[Dict]) -> float:
        """Calculate route optimization index"""
        if not edges:
            return 0.0
        
        # Assume higher number of connections indicates better optimization
        return min(len(edges) * 15, 100)  # Scale to 0-100
    
    def _extract_supply_chain_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract supply chain entities from text"""
        entities = {
            'airports': [],
            'warehouses': [],
            'transport_modes': [],
            'customers': [],
            'routes': []
        }
        
        text_upper = text.upper()
        
        # Extract airport codes
        for code, info in self.expeditors_locations.items():
            if code in text_upper:
                entities['airports'].append({
                    'code': code,
                    'name': info['name'],
                    'type': info['type'],
                    'region': info['region']
                })
        
        # Extract warehouse references
        warehouse_keywords = ['WH', 'WAREHOUSE', 'DISTRIBUTION', 'DC', 'EI TRANSIT']
        for keyword in warehouse_keywords:
            if keyword in text_upper:
                entities['warehouses'].append({
                    'name': keyword,
                    'type': 'warehouse'
                })
        
        # Extract transport modes
        transport_keywords = ['AIRFREIGHT', 'ROAD', 'TRUCK', 'DELIVERY', 'CROSS-BORDER']
        for keyword in transport_keywords:
            if keyword in text_upper:
                entities['transport_modes'].append({
                    'mode': keyword.lower(),
                    'type': 'transport'
                })
        
        # Extract customer references
        customer_keywords = ['CLIENT', 'CUSTOMER', 'COLLECT', 'DELIVERY']
        for keyword in customer_keywords:
            if keyword in text_upper:
                entities['customers'].append({
                    'reference': keyword,
                    'type': 'customer'
                })
        
        return entities
    
    def _generate_network_topology(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Generate network topology from extracted entities"""
        topology = {
            'nodes': [],
            'edges': [],
            'flow_paths': []
        }
        
        node_id = 0
        
        # Add airport nodes
        for airport in entities['airports']:
            topology['nodes'].append({
                'id': f"airport_{node_id}",
                'label': f"{airport['code']} - {airport['name']}",
                'type': 'airport',
                'icon': '✈️',
                'color': '#3498DB',
                'region': airport['region']
            })
            node_id += 1
        
        # Add warehouse nodes
        for warehouse in entities['warehouses']:
            topology['nodes'].append({
                'id': f"warehouse_{node_id}",
                'label': warehouse['name'],
                'type': 'warehouse', 
                'icon': '🏭',
                'color': '#E67E22'
            })
            node_id += 1
        
        # Add customer nodes
        for customer in entities['customers']:
            topology['nodes'].append({
                'id': f"customer_{node_id}",
                'label': customer['reference'],
                'type': 'customer',
                'icon': '🏢',
                'color': '#9B59B6'
            })
            node_id += 1
        
        # Generate connections based on typical supply chain flows
        self._generate_supply_chain_connections(topology)
        
        return topology
    
    def _generate_supply_chain_connections(self, topology: Dict[str, Any]):
        """Generate typical supply chain connections"""
        nodes = topology['nodes']
        edges = []
        
        # Connect airports to warehouses (airfreight flow)
        airports = [n for n in nodes if n['type'] == 'airport']
        warehouses = [n for n in nodes if n['type'] == 'warehouse']
        customers = [n for n in nodes if n['type'] == 'customer']
        
        # Airfreight to warehouse connections
        for airport in airports:
            for warehouse in warehouses:
                edges.append({
                    'source': airport['id'],
                    'target': warehouse['id'],
                    'type': 'airfreight',
                    'label': 'Airfreight',
                    'color': '#3498DB',
                    'weight': 3
                })
        
        # Warehouse to customer connections
        for warehouse in warehouses:
            for customer in customers:
                edges.append({
                    'source': warehouse['id'],
                    'target': customer['id'],
                    'type': 'road_transport',
                    'label': 'Road Transport / Cross-border',
                    'color': '#27AE60',
                    'weight': 2
                })
        
        topology['edges'] = edges
    
    def _create_diagram_data(self, topology: Dict[str, Any]) -> Dict[str, Any]:
        """Create diagram data for visualization"""
        return {
            'title': 'Expeditors Supply Chain Network',
            'nodes': topology['nodes'],
            'edges': topology['edges'],
            'layout': 'hierarchical',
            'theme': 'expeditors_professional',
            'interactive': True,
            'export_formats': ['png', 'svg', 'pdf']
        }
    
    def _generate_insights(self, topology: Dict[str, Any]) -> Dict[str, Any]:
        """Generate supply chain insights and recommendations"""
        nodes = topology['nodes']
        edges = topology['edges']
        
        insights = {
            'network_summary': {
                'total_nodes': len(nodes),
                'total_connections': len(edges),
                'node_types': {}
            },
            'optimization_opportunities': [],
            'risk_assessment': [],
            'recommendations': []
        }
        
        # Count node types
        for node in nodes:
            node_type = node['type']
            insights['network_summary']['node_types'][node_type] = \
                insights['network_summary']['node_types'].get(node_type, 0) + 1
        
        # Generate recommendations
        airports = [n for n in nodes if n['type'] == 'airport']
        warehouses = [n for n in nodes if n['type'] == 'warehouse']
        
        if len(airports) > 3:
            insights['optimization_opportunities'].append(
                "Multiple airports detected - consider hub consolidation for cost optimization"
            )
        
        if len(warehouses) == 1:
            insights['risk_assessment'].append(
                "Single warehouse dependency - consider backup facility for risk mitigation"
            )
        
        insights['recommendations'].extend([
            "Implement real-time tracking across all network nodes",
            "Consider cross-border documentation automation",
            "Evaluate alternative routing options for resilience"
        ])
        
        return insights

# Global instance
network_processor = NetworkDiagramProcessor()