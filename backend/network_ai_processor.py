import os
import json
import logging
from typing import Dict, List, Any, Optional
import httpx
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class AINetworkDiagramProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Enhanced location database for supply chain
        self.locations = {
            # Major Asian Airports & Ports
            'SHA': {'name': 'Shanghai', 'type': 'airport/port', 'region': 'Asia', 'country': 'China'},
            'HKG': {'name': 'Hong Kong', 'type': 'airport/port', 'region': 'Asia', 'country': 'Hong Kong'},
            'SIN': {'name': 'Singapore', 'type': 'airport/port', 'region': 'Asia', 'country': 'Singapore'},
            'NRT': {'name': 'Tokyo', 'type': 'airport', 'region': 'Asia', 'country': 'Japan'},
            'ICN': {'name': 'Seoul', 'type': 'airport', 'region': 'Asia', 'country': 'South Korea'},
            
            # African Airports & Ports
            'JNB': {'name': 'Johannesburg', 'type': 'airport', 'region': 'Africa', 'country': 'South Africa'},
            'CPT': {'name': 'Cape Town', 'type': 'airport/port', 'region': 'Africa', 'country': 'South Africa'},
            'DUR': {'name': 'Durban', 'type': 'airport/port', 'region': 'Africa', 'country': 'South Africa'},
            'PLZ': {'name': 'Port Elizabeth', 'type': 'airport/port', 'region': 'Africa', 'country': 'South Africa'},
            'ELS': {'name': 'East London', 'type': 'airport/port', 'region': 'Africa', 'country': 'South Africa'},
            
            # European Airports & Ports
            'FRA': {'name': 'Frankfurt', 'type': 'airport', 'region': 'Europe', 'country': 'Germany'},
            'CDG': {'name': 'Paris', 'type': 'airport', 'region': 'Europe', 'country': 'France'},
            'LHR': {'name': 'London', 'type': 'airport', 'region': 'Europe', 'country': 'UK'},
            'AMS': {'name': 'Amsterdam', 'type': 'airport/port', 'region': 'Europe', 'country': 'Netherlands'},
            
            # Cross-border destinations
            'BOT': {'name': 'Botswana', 'type': 'country', 'region': 'Africa', 'country': 'Botswana'},
            'NAM': {'name': 'Namibia', 'type': 'country', 'region': 'Africa', 'country': 'Namibia'},
            'ZAM': {'name': 'Zambia', 'type': 'country', 'region': 'Africa', 'country': 'Zambia'},
            'ZIM': {'name': 'Zimbabwe', 'type': 'country', 'region': 'Africa', 'country': 'Zimbabwe'},
            
            # Facilities
            'RTS': {'name': 'Transit Shed', 'type': 'facility', 'region': 'Africa', 'country': 'South Africa'},
            'DC': {'name': 'Distribution Center', 'type': 'facility', 'region': 'Africa', 'country': 'South Africa'},
        }
        
        # Transport mode mapping
        self.transport_modes = {
            'airfreight': {'icon': 'plane', 'color': '#3498DB', 'style': 'solid'},
            'seafreight': {'icon': 'ship', 'color': '#2ECC71', 'style': 'solid'},
            'road': {'icon': 'truck', 'color': '#E74C3C', 'style': 'solid'},
            'rail': {'icon': 'train', 'color': '#9B59B6', 'style': 'solid'},
            'draw': {'icon': 'move', 'color': '#F39C12', 'style': 'dashed'},
            'collect': {'icon': 'pickup', 'color': '#34495E', 'style': 'dotted'},
            'deliver': {'icon': 'delivery', 'color': '#1ABC9C', 'style': 'solid'},
        }
    
    async def process_input(self, input_type: str, content: str, user_context: Dict = None) -> Dict[str, Any]:
        """Process different input types and generate network diagram data"""
        try:
            if input_type == 'voice_transcript':
                return await self._process_voice_transcript(content, user_context)
            elif input_type == 'text_description':
                return await self._process_text_description(content, user_context)
            elif input_type == 'csv_data':
                return await self._process_csv_data(content, user_context)
            else:
                raise ValueError(f"Unsupported input type: {input_type}")
                
        except Exception as e:
            self.logger.error(f"Error processing input: {str(e)}")
            raise
    
    async def _process_voice_transcript(self, transcript: str, user_context: Dict = None) -> Dict[str, Any]:
        """Process voice transcript to extract supply chain network"""
        prompt = f"""
        Analyze this supply chain voice transcript and extract a network diagram structure.
        
        Transcript: {transcript}
        
        Extract and structure the following:
        1. Nodes: Suppliers, airports, ports, distribution centers, customers, cross-border destinations
        2. Edges: Transport flows between nodes with mode (airfreight, seafreight, road, rail, draw, collect, deliver)
        3. Regional groupings: Group related nodes by function (suppliers, facilities, destinations)
        
        Return a JSON structure with:
        {{
            "nodes": [
                {{"id": "SHA", "label": "Shanghai Supplier", "type": "supplier", "region": "Asia"}},
                {{"id": "JNB", "label": "Johannesburg Airport", "type": "airport", "region": "Africa"}}
            ],
            "edges": [
                {{"from": "SHA", "to": "JNB", "transport": "airfreight", "label": "Airfreight"}},
                {{"from": "JNB", "to": "DC", "transport": "road", "label": "Road transport"}}
            ],
            "regions": [
                {{"name": "Suppliers", "nodes": ["SHA", "HKG"]}},
                {{"name": "Distribution", "nodes": ["DC", "DUR"]}}
            ],
            "title": "Supply Chain Network",
            "description": "Brief description of the network"
        }}
        
        Focus on logistics terminology: suppliers, airfreight, seafreight, distribution centers, cross-border, transit sheds.
        """
        
        return await self._call_ai_service(prompt)
    
    async def _process_text_description(self, description: str, user_context: Dict = None) -> Dict[str, Any]:
        """Process text description to create network diagram"""
        prompt = f"""
        Convert this supply chain text description into a network diagram structure.
        
        Description: {description}
        
        Create a JSON structure representing the supply chain network with nodes and edges.
        Include transport modes (airfreight, seafreight, road, rail) and facility types (supplier, airport, port, DC, customer).
        
        Return the same JSON format as specified with nodes, edges, regions, title, and description.
        Make it optimized for supply chain visualization with proper groupings.
        """
        
        return await self._call_ai_service(prompt)
    
    async def _process_csv_data(self, csv_content: str, user_context: Dict = None) -> Dict[str, Any]:
        """Process CSV data to create network diagram"""
        try:
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                raise ValueError("CSV must have header and at least one data row")
            
            headers = [h.strip().lower() for h in lines[0].split(',')]
            
            # Expected columns: from, to, transport, notes/label
            nodes = set()
            edges = []
            
            for line in lines[1:]:
                values = [v.strip() for v in line.split(',')]
                if len(values) >= 2:
                    from_node = values[0]
                    to_node = values[1]
                    transport = values[2] if len(values) > 2 else 'road'
                    label = values[3] if len(values) > 3 else f"{transport} transport"
                    
                    nodes.add(from_node)
                    nodes.add(to_node)
                    
                    edges.append({
                        "from": from_node,
                        "to": to_node,
                        "transport": transport,
                        "label": label
                    })
            
            # Create nodes with enhanced info
            node_list = []
            for node in nodes:
                location_info = self.locations.get(node, {})
                node_list.append({
                    "id": node,
                    "label": location_info.get('name', node),
                    "type": location_info.get('type', 'location'),
                    "region": location_info.get('region', 'Unknown')
                })
            
            # Create basic regional grouping
            regions = []
            asia_nodes = [n["id"] for n in node_list if n["region"] == "Asia"]
            africa_nodes = [n["id"] for n in node_list if n["region"] == "Africa"]
            europe_nodes = [n["id"] for n in node_list if n["region"] == "Europe"]
            
            if asia_nodes:
                regions.append({"name": "Asian Suppliers", "nodes": asia_nodes})
            if africa_nodes:
                regions.append({"name": "African Operations", "nodes": africa_nodes})
            if europe_nodes:
                regions.append({"name": "European Suppliers", "nodes": europe_nodes})
            
            return {
                "nodes": node_list,
                "edges": edges,
                "regions": regions,
                "title": "Supply Chain Network from CSV",
                "description": f"Network with {len(node_list)} nodes and {len(edges)} connections"
            }
            
        except Exception as e:
            self.logger.error(f"Error processing CSV: {str(e)}")
            raise ValueError(f"Invalid CSV format: {str(e)}")
    
    async def _call_ai_service(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API to process prompt"""
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("WHISPER_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.3
                    },
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                response.raise_for_status()
                
                ai_response = response.json()
                content = ai_response["choices"][0]["message"]["content"]
                
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    # Fallback: create basic structure
                    return {
                        "nodes": [],
                        "edges": [],
                        "regions": [],
                        "title": "Supply Chain Network",
                        "description": "Generated from AI analysis",
                        "raw_response": content
                    }
                    
        except Exception as e:
            self.logger.error(f"AI service call failed: {str(e)}")
            raise
    
    def generate_mermaid_diagram(self, network_data: Dict[str, Any]) -> str:
        """Generate Mermaid diagram syntax from network data"""
        try:
            nodes = network_data.get('nodes', [])
            edges = network_data.get('edges', [])
            regions = network_data.get('regions', [])
            
            mermaid_lines = ["graph TD"]
            
            # Add regional subgraphs
            for region in regions:
                region_name = region['name'].replace(' ', '_')
                mermaid_lines.append(f"    subgraph {region_name}[\"{region['name']}\"]")
                for node_id in region['nodes']:
                    node = next((n for n in nodes if n['id'] == node_id), None)
                    if node:
                        node_label = node['label'].replace('"', "'")
                        mermaid_lines.append(f"        {node_id}[\"{node_label}\"]")
                mermaid_lines.append("    end")
                mermaid_lines.append("")
            
            # Add standalone nodes (not in regions)
            region_nodes = set()
            for region in regions:
                region_nodes.update(region['nodes'])
            
            for node in nodes:
                if node['id'] not in region_nodes:
                    node_label = node['label'].replace('"', "'")
                    mermaid_lines.append(f"    {node['id']}[\"{node_label}\"]")
            
            mermaid_lines.append("")
            
            # Add edges with styling
            for edge in edges:
                transport = edge.get('transport', 'road')
                label = edge.get('label', transport)
                
                # Style based on transport mode
                if transport == 'airfreight':
                    arrow_style = "-->|✈️ " + label + "|"
                elif transport == 'seafreight':
                    arrow_style = "-->|🚢 " + label + "|"
                elif transport == 'road':
                    arrow_style = "-->|🚛 " + label + "|"
                elif transport == 'rail':
                    arrow_style = "-->|🚂 " + label + "|"
                elif transport == 'draw':
                    arrow_style = "-.->|📦 " + label + "|"
                else:
                    arrow_style = f"-->|{label}|"
                
                mermaid_lines.append(f"    {edge['from']} {arrow_style} {edge['to']}")
            
            # Add styling for better visualization
            mermaid_lines.extend([
                "",
                "    classDef supplier fill:#e1f5fe,stroke:#01579b,stroke-width:2px",
                "    classDef airport fill:#f3e5f5,stroke:#4a148c,stroke-width:2px", 
                "    classDef facility fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px",
                "    classDef customer fill:#fff3e0,stroke:#e65100,stroke-width:2px"
            ])
            
            return '\n'.join(mermaid_lines)
            
        except Exception as e:
            self.logger.error(f"Error generating Mermaid diagram: {str(e)}")
            return "graph TD\n    Error[\"Error generating diagram\"]"
    
    def generate_csv_template(self) -> str:
        """Generate CSV template for user input"""
        template = """From,To,Transport,Notes
SHA,JNB,airfreight,Supplier to airport
HKG,JNB,airfreight,Supplier to airport  
JNB,RTS,draw,To transit shed
RTS,DC,collect,To distribution center
DC,DUR,road,To regional DC
DC,CPT,road,To regional DC
DC,BOT,road,Cross-border delivery
DC,NAM,air,Cross-border airfreight"""
        
        return template