import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Download, Maximize2, RotateCcw, Zap } from 'lucide-react';

const FlowingNetworkVisualization = ({ networkData, title = "Supply Chain Network Flow" }) => {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const [isAnimating, setIsAnimating] = useState(true);
  const [hoveredNode, setHoveredNode] = useState(null);

  useEffect(() => {
    if (!networkData || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    
    // Set canvas size for high DPI
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    
    // Animation variables
    let animationTime = 0;
    const nodes = processNetworkNodes(networkData);
    const flows = processNetworkFlows(networkData, nodes);

    const animate = () => {
      if (!isAnimating) return;
      
      animationTime += 0.02;
      
      // Clear canvas with dark starry background
      drawStarryBackground(ctx, canvas.width / dpr, canvas.height / dpr, animationTime);
      
      // Draw flowing connections
      flows.forEach((flow, index) => {
        drawFlowingCurve(ctx, flow, animationTime + index * 0.3);
      });
      
      // Draw glowing nodes
      nodes.forEach(node => {
        drawGlowingNode(ctx, node, animationTime);
      });
      
      // Draw labels
      nodes.forEach(node => {
        drawNodeLabel(ctx, node);
      });
      
      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [networkData, isAnimating]);

  const processNetworkNodes = (data) => {
    if (!data?.network_topology?.nodes) return [];
    
    return data.network_topology.nodes.map((node, index) => {
      const angle = (index / data.network_topology.nodes.length) * 2 * Math.PI;
      const radius = 150 + Math.random() * 100;
      
      return {
        id: node.id,
        label: node.label,
        type: node.type,
        x: 400 + Math.cos(angle) * radius,
        y: 300 + Math.sin(angle) * radius,
        color: getNodeColor(node.type),
        glowColor: getGlowColor(node.type),
        size: getNodeSize(node.type)
      };
    });
  };

  const processNetworkFlows = (data, nodes) => {
    if (!data?.network_topology?.edges || !nodes.length) return [];
    
    return data.network_topology.edges.map(edge => {
      const sourceNode = nodes.find(n => n.id === edge.source);
      const targetNode = nodes.find(n => n.id === edge.target);
      
      if (!sourceNode || !targetNode) return null;
      
      return {
        source: sourceNode,
        target: targetNode,
        type: edge.type,
        color: getFlowColor(edge.type),
        width: getFlowWidth(edge.type),
        intensity: Math.random() * 0.5 + 0.5
      };
    }).filter(Boolean);
  };

  const drawStarryBackground = (ctx, width, height, time) => {
    // Create gradient background
    const gradient = ctx.createRadialGradient(width/2, height/2, 0, width/2, height/2, width);
    gradient.addColorStop(0, 'rgba(10, 10, 30, 1)');
    gradient.addColorStop(0.5, 'rgba(5, 5, 20, 1)');
    gradient.addColorStop(1, 'rgba(0, 0, 10, 1)');
    
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
    
    // Add twinkling stars
    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
    for (let i = 0; i < 100; i++) {
      const x = (i * 137.5) % width;
      const y = (i * 73.3) % height;
      const twinkle = Math.sin(time * 2 + i) * 0.5 + 0.5;
      const size = twinkle * 2;
      
      ctx.globalAlpha = twinkle;
      ctx.beginPath();
      ctx.arc(x, y, size, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  };

  const drawFlowingCurve = (ctx, flow, time) => {
    const { source, target, color, width, intensity } = flow;
    
    // Create control points for smooth curves
    const midX = (source.x + target.x) / 2;
    const midY = (source.y + target.y) / 2;
    const distance = Math.sqrt((target.x - source.x) ** 2 + (target.y - source.y) ** 2);
    
    // Add some curve variation
    const curvature = Math.sin(time * 0.5) * 50 + distance * 0.3;
    const controlX = midX + Math.sin(time * 0.3) * 30;
    const controlY = midY - curvature;
    
    // Draw main flowing curve
    ctx.lineWidth = width;
    ctx.lineCap = 'round';
    
    // Create gradient along the curve
    const gradient = ctx.createLinearGradient(source.x, source.y, target.x, target.y);
    const baseColor = hexToRgb(color);
    const alpha = intensity * (Math.sin(time * 2) * 0.3 + 0.7);
    
    gradient.addColorStop(0, `rgba(${baseColor.r}, ${baseColor.g}, ${baseColor.b}, 0.1)`);
    gradient.addColorStop(0.5, `rgba(${baseColor.r}, ${baseColor.g}, ${baseColor.b}, ${alpha})`);
    gradient.addColorStop(1, `rgba(${baseColor.r}, ${baseColor.g}, ${baseColor.b}, 0.1)`);
    
    // Draw glowing effect
    ctx.shadowColor = color;
    ctx.shadowBlur = 20;
    ctx.strokeStyle = gradient;
    
    ctx.beginPath();
    ctx.moveTo(source.x, source.y);
    ctx.quadraticCurveTo(controlX, controlY, target.x, target.y);
    ctx.stroke();
    
    // Add flowing particles
    drawFlowingParticles(ctx, flow, time);
    
    ctx.shadowBlur = 0;
  };

  const drawFlowingParticles = (ctx, flow, time) => {
    const { source, target, color } = flow;
    const numParticles = 5;
    
    for (let i = 0; i < numParticles; i++) {
      const progress = ((time * 0.5 + i * 0.2) % 1);
      const x = source.x + (target.x - source.x) * progress;
      const y = source.y + (target.y - source.y) * progress;
      
      // Add curve effect to particles
      const midX = (source.x + target.x) / 2;
      const midY = (source.y + target.y) / 2;
      const distance = Math.sqrt((target.x - source.x) ** 2 + (target.y - source.y) ** 2);
      const curvature = Math.sin(time * 0.5) * 50 + distance * 0.3;
      
      const curveX = x + Math.sin(progress * Math.PI) * (midX - x + Math.sin(time * 0.3) * 30) * 0.1;
      const curveY = y + Math.sin(progress * Math.PI) * (-curvature) * 0.1;
      
      const baseColor = hexToRgb(color);
      const alpha = Math.sin(progress * Math.PI) * 0.8;
      
      ctx.fillStyle = `rgba(${baseColor.r}, ${baseColor.g}, ${baseColor.b}, ${alpha})`;
      ctx.shadowColor = color;
      ctx.shadowBlur = 10;
      
      ctx.beginPath();
      ctx.arc(curveX, curveY, 3, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.shadowBlur = 0;
  };

  const drawGlowingNode = (ctx, node, time) => {
    const { x, y, size, color, glowColor } = node;
    const pulseScale = Math.sin(time * 3) * 0.1 + 1;
    const nodeSize = size * pulseScale;
    
    // Draw outer glow
    const glowGradient = ctx.createRadialGradient(x, y, 0, x, y, nodeSize * 3);
    glowGradient.addColorStop(0, glowColor);
    glowGradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.1)');
    glowGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
    
    ctx.fillStyle = glowGradient;
    ctx.beginPath();
    ctx.arc(x, y, nodeSize * 3, 0, Math.PI * 2);
    ctx.fill();
    
    // Draw main node
    const nodeGradient = ctx.createRadialGradient(x, y, 0, x, y, nodeSize);
    nodeGradient.addColorStop(0, 'rgba(255, 255, 255, 0.9)');
    nodeGradient.addColorStop(0.7, color);
    nodeGradient.addColorStop(1, 'rgba(0, 0, 0, 0.3)');
    
    ctx.fillStyle = nodeGradient;
    ctx.shadowColor = glowColor;
    ctx.shadowBlur = 15;
    
    ctx.beginPath();
    ctx.arc(x, y, nodeSize, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.shadowBlur = 0;
  };

  const drawNodeLabel = (ctx, node) => {
    const { x, y, label, type } = node;
    
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.font = 'bold 12px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    // Draw label background
    const metrics = ctx.measureText(label);
    const padding = 8;
    const bgX = x - metrics.width / 2 - padding;
    const bgY = y + 40 - 6;
    const bgWidth = metrics.width + padding * 2;
    const bgHeight = 12;
    
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(bgX, bgY, bgWidth, bgHeight);
    
    // Draw text
    ctx.fillStyle = 'white';
    ctx.fillText(label, x, y + 40);
    
    // Draw type badge
    ctx.font = '10px Inter, sans-serif';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
    ctx.fillText(type.toUpperCase(), x, y + 55);
  };

  const getNodeColor = (type) => {
    const colors = {
      airport: '#3498DB',
      warehouse: '#E67E22',
      customer: '#9B59B6',
      port: '#27AE60',
      distribution_center: '#E74C3C',
      default: '#7F8C8D'
    };
    return colors[type] || colors.default;
  };

  const getGlowColor = (type) => {
    const colors = {
      airport: 'rgba(52, 152, 219, 0.6)',
      warehouse: 'rgba(230, 126, 34, 0.6)',
      customer: 'rgba(155, 89, 182, 0.6)',
      port: 'rgba(39, 174, 96, 0.6)',
      distribution_center: 'rgba(231, 76, 60, 0.6)',
      default: 'rgba(127, 140, 141, 0.6)'
    };
    return colors[type] || colors.default;
  };

  const getNodeSize = (type) => {
    const sizes = {
      airport: 20,
      warehouse: 18,
      customer: 15,
      port: 22,
      distribution_center: 17,
      default: 12
    };
    return sizes[type] || sizes.default;
  };

  const getFlowColor = (type) => {
    const colors = {
      airfreight: '#3498DB',
      road_transport: '#27AE60',
      transportation: '#2ECC71',
      storage: '#F39C12',
      processing: '#E74C3C',
      default: '#BDC3C7'
    };
    return colors[type] || colors.default;
  };

  const getFlowWidth = (type) => {
    const widths = {
      airfreight: 4,
      road_transport: 3,
      transportation: 3,
      storage: 2,
      processing: 2,
      default: 2
    };
    return widths[type] || widths.default;
  };

  const hexToRgb = (hex) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : { r: 255, g: 255, b: 255 };
  };

  const exportVisualization = () => {
    const canvas = canvasRef.current;
    const link = document.createElement('a');
    link.download = `${title.replace(/\s+/g, '_')}_network_diagram.png`;
    link.href = canvas.toDataURL();
    link.click();
  };

  const toggleAnimation = () => {
    setIsAnimating(!isAnimating);
  };

  if (!networkData) {
    return (
      <Card className="w-full h-96 flex items-center justify-center">
        <CardContent>
          <p className="text-gray-500">No network data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full shadow-2xl border-0 bg-black/90 backdrop-blur-sm overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div>
          <CardTitle className="text-white flex items-center space-x-2">
            <Zap className="w-5 h-5 text-blue-400" />
            <span>{title}</span>
          </CardTitle>
          <p className="text-gray-400 text-sm mt-1">Dynamic supply chain network visualization</p>
        </div>
        <div className="flex space-x-2">
          <Button
            onClick={toggleAnimation}
            variant="outline"
            size="sm"
            className="bg-white/10 border-white/20 text-white hover:bg-white/20"
          >
            <RotateCcw className="w-4 h-4" />
          </Button>
          <Button
            onClick={exportVisualization}
            variant="outline"
            size="sm"
            className="bg-white/10 border-white/20 text-white hover:bg-white/20"
          >
            <Download className="w-4 h-4" />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="p-0">
        <div className="relative">
          <canvas
            ref={canvasRef}
            className="w-full h-96 cursor-pointer"
            style={{ background: 'transparent' }}
          />
          
          {/* Network Stats Overlay */}
          <div className="absolute top-4 left-4 space-y-2">
            <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/30">
              {networkData.network_topology?.nodes?.length || 0} Nodes
            </Badge>
            <Badge className="bg-green-500/20 text-green-300 border-green-500/30">
              {networkData.network_topology?.edges?.length || 0} Connections
            </Badge>
            <Badge className="bg-purple-500/20 text-purple-300 border-purple-500/30">
              {isAnimating ? 'Live' : 'Paused'}
            </Badge>
          </div>
          
          {/* Controls */}
          <div className="absolute bottom-4 right-4 text-xs text-gray-400">
            <p>✨ Dynamic visualization • Click to interact</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default FlowingNetworkVisualization;