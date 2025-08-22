import os
import json
import logging
from typing import Dict, List, Any, Optional
from .providers import stt_transcribe, ocr_read
from .storage import create_presigned_get_url

logger = logging.getLogger(__name__)

class NetworkDiagramProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Expeditors-specific locations and codes
        self.expeditors_locations = {
            'SHA': {'name': 'Shanghai', 'type': 'airport', 'region': 'Asia'},
            'PVG': {'name': 'Shanghai Pudong', 'type': 'airport', 'region': 'Asia'},
            'JNB': {'name': 'Johannesburg OR Tambo', 'type': 'airport', 'region': 'Africa'},
            'HKG': {'name': 'Hong Kong International', 'type': 'airport', 'region': 'Asia'},
            'FRA': {'name': 'Frankfurt Main', 'type': 'airport', 'region': 'Europe'},
            'CDG': {'name': 'Paris Charles de Gaulle', 'type': 'airport', 'region': 'Europe'},
            'ORT': {'name': 'OR Tambo International', 'type': 'airport', 'region': 'Africa'},
        }
        
        # Supply chain flow patterns
        self.flow_patterns = {
            'airfreight': {
                'icon': '✈️',
                'color': '#3498DB',
                'typical_routes': ['SHA-JNB', 'HKG-JNB', 'FRA-JNB', 'CDG-JNB']
            },
            'warehouse': {
                'icon': '🏭',
                'color': '#E67E22', 
                'operations': ['EI Transit WH', 'Distribution Center', 'Cross-dock']
            },
            'road_transport': {
                'icon': '🚛',
                'color': '#27AE60',
                'services': ['Local delivery', 'Cross-border', 'Last mile']
            },
            'customs': {
                'icon': '📋',
                'color': '#8E44AD',
                'processes': ['Clearance', 'Documentation', 'Inspection']
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