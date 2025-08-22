"""
Expeditors Network Diagram Templates
Based on PowerPoint samples - Professional presentation layouts
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class NetworkTemplate:
    name: str
    layout_type: str
    color_scheme: Dict[str, str]
    node_styles: Dict[str, Any]
    connection_styles: Dict[str, Any]
    branding: Dict[str, str]

class ExpeditorsTemplateEngine:
    def __init__(self):
        self.templates = self._initialize_templates()
        
    def _initialize_templates(self) -> Dict[str, NetworkTemplate]:
        """Initialize professional Expeditors templates based on PowerPoint samples"""
        
        return {
            "supply_chain_flow": NetworkTemplate(
                name="Supply Chain Flow",
                layout_type="left_to_right_flow",
                color_scheme={
                    "primary_blue": "#1B4F72",
                    "accent_orange": "#E67E22", 
                    "success_green": "#27AE60",
                    "warning_red": "#E74C3C",
                    "neutral_gray": "#85929E",
                    "background": "#FFFFFF",
                    "text_primary": "#2C3E50",
                    "text_secondary": "#7F8C8D"
                },
                node_styles={
                    "origin": {
                        "shape": "rectangle_rounded",
                        "color": "#1B4F72",
                        "border": "#154360",
                        "text_color": "#FFFFFF",
                        "icon": "plane",
                        "size": "large"
                    },
                    "hub": {
                        "shape": "hexagon",
                        "color": "#E67E22",
                        "border": "#D35400",
                        "text_color": "#FFFFFF", 
                        "icon": "warehouse",
                        "size": "large"
                    },
                    "destination": {
                        "shape": "circle",
                        "color": "#27AE60",
                        "border": "#229954",
                        "text_color": "#FFFFFF",
                        "icon": "building",
                        "size": "medium"
                    },
                    "process": {
                        "shape": "diamond",
                        "color": "#8E44AD",
                        "border": "#7D3C98",
                        "text_color": "#FFFFFF",
                        "icon": "gear",
                        "size": "small"
                    }
                },
                connection_styles={
                    "primary_flow": {
                        "style": "thick_arrow",
                        "color": "#1B4F72",
                        "width": 4,
                        "pattern": "solid",
                        "animation": "flow_dots"
                    },
                    "secondary_flow": {
                        "style": "medium_arrow", 
                        "color": "#E67E22",
                        "width": 3,
                        "pattern": "solid",
                        "animation": "glow_pulse"
                    },
                    "information_flow": {
                        "style": "dashed_line",
                        "color": "#85929E",
                        "width": 2,
                        "pattern": "dashed",
                        "animation": "none"
                    }
                },
                branding={
                    "logo_position": "top_right",
                    "company_colors": True,
                    "footer_text": "Expeditors Supply Chain Solutions",
                    "watermark": "expeditors_subtle"
                }
            ),
            
            "hub_and_spoke": NetworkTemplate(
                name="Hub and Spoke Network",
                layout_type="radial_hub",
                color_scheme={
                    "hub_primary": "#E67E22",
                    "spoke_blue": "#3498DB", 
                    "spoke_green": "#27AE60",
                    "spoke_purple": "#8E44AD",
                    "connection_gray": "#BDC3C7",
                    "background": "#F8F9FA",
                    "text_primary": "#2C3E50",
                    "accent_gold": "#F39C12"
                },
                node_styles={
                    "central_hub": {
                        "shape": "large_circle",
                        "color": "#E67E22",
                        "border": "#D35400",
                        "text_color": "#FFFFFF",
                        "icon": "hub",
                        "size": "extra_large",
                        "glow": True
                    },
                    "regional_hub": {
                        "shape": "circle",
                        "color": "#3498DB",
                        "border": "#2980B9",
                        "text_color": "#FFFFFF",
                        "icon": "location",
                        "size": "large"
                    },
                    "endpoint": {
                        "shape": "square_rounded",
                        "color": "#27AE60",
                        "border": "#229954",
                        "text_color": "#FFFFFF",
                        "icon": "marker",
                        "size": "medium"
                    }
                },
                connection_styles={
                    "hub_connection": {
                        "style": "curved_arrow",
                        "color": "#E67E22",
                        "width": 3,
                        "pattern": "solid",
                        "animation": "bi_directional_flow"
                    },
                    "spoke_connection": {
                        "style": "straight_line",
                        "color": "#3498DB",
                        "width": 2,
                        "pattern": "solid",
                        "animation": "outbound_flow"
                    }
                },
                branding={
                    "logo_position": "bottom_right",
                    "company_colors": True,
                    "footer_text": "Global Network • Local Expertise",
                    "watermark": "expeditors_network"
                }
            ),
            
            "multi_modal_transport": NetworkTemplate(
                name="Multi-Modal Transport",
                layout_type="layered_horizontal",
                color_scheme={
                    "air_blue": "#3498DB",
                    "ocean_navy": "#1B4F72",
                    "road_green": "#27AE60",
                    "rail_purple": "#8E44AD",
                    "warehouse_orange": "#E67E22",
                    "customs_red": "#E74C3C",
                    "background": "#FAFBFC"
                },
                node_styles={
                    "airport": {
                        "shape": "runway_icon",
                        "color": "#3498DB",
                        "border": "#2980B9",
                        "text_color": "#FFFFFF",
                        "icon": "plane_takeoff",
                        "size": "large"
                    },
                    "seaport": {
                        "shape": "port_icon",
                        "color": "#1B4F72", 
                        "border": "#154360",
                        "text_color": "#FFFFFF",
                        "icon": "ship",
                        "size": "large"
                    },
                    "distribution_center": {
                        "shape": "warehouse_icon",
                        "color": "#E67E22",
                        "border": "#D35400",
                        "text_color": "#FFFFFF",
                        "icon": "warehouse_modern",
                        "size": "large"
                    },
                    "customs": {
                        "shape": "shield_icon",
                        "color": "#E74C3C",
                        "border": "#C0392B",
                        "text_color": "#FFFFFF",
                        "icon": "customs_stamp",
                        "size": "medium"
                    }
                },
                connection_styles={
                    "air_route": {
                        "style": "flight_path",
                        "color": "#3498DB",
                        "width": 3,
                        "pattern": "flight_dots",
                        "animation": "airplane_movement"
                    },
                    "ocean_route": {
                        "style": "wave_line",
                        "color": "#1B4F72",
                        "width": 4,
                        "pattern": "wave_pattern",
                        "animation": "ship_movement"
                    },
                    "road_route": {
                        "style": "highway_line",
                        "color": "#27AE60",
                        "width": 3,
                        "pattern": "road_dashes",
                        "animation": "truck_movement"
                    }
                },
                branding={
                    "logo_position": "header_center",
                    "company_colors": True,
                    "footer_text": "Connecting Global Commerce",
                    "mode_legends": True
                }
            )
        }
    
    def generate_network_config(self, template_name: str, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate network configuration based on template and data"""
        
        if template_name not in self.templates:
            template_name = "supply_chain_flow"  # Default fallback
            
        template = self.templates[template_name]
        
        # Analyze network data to determine best layout
        nodes = network_data.get("network_topology", {}).get("nodes", [])
        edges = network_data.get("network_topology", {}).get("edges", [])
        
        config = {
            "template_name": template.name,
            "layout": self._generate_layout_config(template, nodes, edges),
            "styling": self._generate_styling_config(template),
            "animations": self._generate_animation_config(template),
            "branding": template.branding,
            "export_settings": {
                "formats": ["png", "svg", "pdf", "pptx"],
                "resolutions": ["1920x1080", "3840x2160", "print_ready"],
                "themes": ["light", "dark", "presentation"]
            }
        }
        
        return config
    
    def _generate_layout_config(self, template: NetworkTemplate, nodes: List[Any], edges: List[Any]) -> Dict[str, Any]:
        """Generate layout configuration based on template and network structure"""
        
        layout_configs = {
            "left_to_right_flow": {
                "algorithm": "hierarchical",
                "direction": "horizontal",
                "node_spacing": {"x": 200, "y": 100},
                "layer_separation": 150,
                "alignment": "center"
            },
            "radial_hub": {
                "algorithm": "radial",
                "center_node": "auto_detect_hub",
                "radius_layers": [100, 200, 300],
                "angular_spacing": "auto",
                "hub_emphasis": True
            },
            "layered_horizontal": {
                "algorithm": "layered",
                "layers": ["origin", "transit", "processing", "destination"],
                "layer_height": 120,
                "intra_layer_spacing": 80,
                "inter_layer_spacing": 180
            }
        }
        
        return layout_configs.get(template.layout_type, layout_configs["left_to_right_flow"])
    
    def _generate_styling_config(self, template: NetworkTemplate) -> Dict[str, Any]:
        """Generate styling configuration from template"""
        
        return {
            "color_palette": template.color_scheme,
            "node_styles": template.node_styles,
            "connection_styles": template.connection_styles,
            "typography": {
                "primary_font": "Segoe UI",
                "secondary_font": "Arial",
                "header_size": 16,
                "body_size": 12,
                "caption_size": 10
            },
            "effects": {
                "drop_shadows": True,
                "gradients": True,
                "transparency": 0.9,
                "border_radius": 8
            }
        }
    
    def _generate_animation_config(self, template: NetworkTemplate) -> Dict[str, Any]:
        """Generate animation configuration"""
        
        return {
            "enabled": True,
            "flow_animations": [
                {
                    "type": "particle_flow",
                    "speed": 2.0,
                    "particle_count": 5,
                    "particle_size": 3
                },
                {
                    "type": "glow_pulse",
                    "duration": 3000,
                    "intensity": 0.8
                },
                {
                    "type": "connection_draw",
                    "duration": 2000,
                    "delay": 500
                }
            ],
            "interaction_effects": {
                "hover_zoom": 1.1,
                "click_highlight": True,
                "selection_glow": True
            }
        }
    
    def get_template_preview(self, template_name: str) -> Dict[str, Any]:
        """Get template preview information"""
        
        if template_name not in self.templates:
            return {"error": "Template not found"}
            
        template = self.templates[template_name]
        
        return {
            "name": template.name,
            "layout_type": template.layout_type,
            "best_for": self._get_template_use_cases(template_name),
            "color_preview": template.color_scheme,
            "sample_nodes": 3,
            "sample_connections": 2,
            "professional_grade": True
        }
    
    def _get_template_use_cases(self, template_name: str) -> List[str]:
        """Get use cases for each template"""
        
        use_cases = {
            "supply_chain_flow": [
                "Linear supply chain processes",
                "Import/Export workflows", 
                "Step-by-step logistics flows",
                "Process documentation"
            ],
            "hub_and_spoke": [
                "Distribution network design",
                "Regional hub planning",
                "Centralized operations",
                "Service coverage maps"
            ],
            "multi_modal_transport": [
                "Intermodal transport planning",
                "Mode comparison analysis",
                "Route optimization",
                "Transport cost modeling"
            ]
        }
        
        return use_cases.get(template_name, ["General network visualization"])

# Global template engine instance
template_engine = ExpeditorsTemplateEngine()