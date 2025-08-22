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
        """Process network diagram input (voice or sketch)"""
        try:
            if input_type == "audio":
                result = await stt_transcribe(file_url)
                raw_text = result.get("text", "")
            elif input_type == "image":
                result = await ocr_read(file_url)
                raw_text = result.get("text", "")
            else:
                raise ValueError(f"Unsupported input type: {input_type}")
            
            # Extract supply chain entities
            entities = self._extract_supply_chain_entities(raw_text)
            
            # Generate network topology
            network_topology = self._generate_network_topology(entities)
            
            # Create visual diagram data
            diagram_data = self._create_diagram_data(network_topology)
            
            # Generate insights and recommendations
            insights = self._generate_insights(network_topology)
            
            return {
                "raw_input": raw_text,
                "entities": entities,
                "network_topology": network_topology,
                "diagram_data": diagram_data,
                "insights": insights,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Error processing network input: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }
    
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