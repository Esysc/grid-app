import React, { useEffect, useRef } from 'react';
import './GridTopology.css';

const GridTopology = () => {
  const canvasRef = useRef(null);

  // Grid nodes representing substations and junction points
  const nodes = [
    { id: 'main-hub', x: 200, y: 150, label: 'Main Hub', type: 'hub' },
    { id: 'substation-1', x: 100, y: 50, label: 'Substation 1', type: 'substation' },
    { id: 'substation-2', x: 300, y: 50, label: 'Substation 2', type: 'substation' },
    { id: 'transformer-1', x: 50, y: 250, label: 'Transformer 1', type: 'transformer' },
    { id: 'transformer-2', x: 350, y: 250, label: 'Transformer 2', type: 'transformer' },
    { id: 'feeder-1', x: 50, y: 350, label: 'Feeder 1', type: 'feeder' },
    { id: 'feeder-2', x: 200, y: 350, label: 'Feeder 2', type: 'feeder' },
    { id: 'feeder-3', x: 350, y: 350, label: 'Feeder 3', type: 'feeder' },
  ];

  // Connections between nodes
  const connections = [
    { from: 'substation-1', to: 'main-hub' },
    { from: 'substation-2', to: 'main-hub' },
    { from: 'main-hub', to: 'transformer-1' },
    { from: 'main-hub', to: 'transformer-2' },
    { from: 'transformer-1', to: 'feeder-1' },
    { from: 'transformer-1', to: 'feeder-2' },
    { from: 'transformer-2', to: 'feeder-2' },
    { from: 'transformer-2', to: 'feeder-3' },
  ];

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw grid background
    ctx.strokeStyle = '#2a2a4e';
    ctx.lineWidth = 0.5;
    for (let x = 0; x < canvas.width; x += 20) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += 20) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Draw connections
    ctx.strokeStyle = '#4fc3f7';
    ctx.lineWidth = 2;
    connections.forEach((conn) => {
      const fromNode = nodes.find((n) => n.id === conn.from);
      const toNode = nodes.find((n) => n.id === conn.to);
      if (fromNode && toNode) {
        ctx.beginPath();
        ctx.moveTo(fromNode.x, fromNode.y);
        ctx.lineTo(toNode.x, toNode.y);
        ctx.stroke();
      }
    });

    // Draw nodes
    nodes.forEach((node) => {
      // Node circle
      ctx.fillStyle =
        node.type === 'hub'
          ? '#ff6b6b'
          : node.type === 'substation'
            ? '#4fc3f7'
            : node.type === 'transformer'
              ? '#ffd700'
              : '#4caf50';
      ctx.beginPath();
      ctx.arc(node.x, node.y, 15, 0, Math.PI * 2);
      ctx.fill();

      // Node border
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Node label
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 10px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(node.label, node.x, node.y + 30);
    });

    // Draw legend
    const legendX = canvas.width - 150;
    const legendY = 10;
    const legendItems = [
      { label: 'Main Hub', color: '#ff6b6b' },
      { label: 'Substation', color: '#4fc3f7' },
      { label: 'Transformer', color: '#ffd700' },
      { label: 'Feeder', color: '#4caf50' },
    ];

    ctx.font = 'bold 12px Arial';
    ctx.fillStyle = '#fff';
    ctx.fillText('Legend', legendX, legendY);

    legendItems.forEach((item, i) => {
      const y = legendY + 20 + i * 20;
      ctx.fillStyle = item.color;
      ctx.fillRect(legendX, y, 12, 12);
      ctx.fillStyle = '#fff';
      ctx.font = '11px Arial';
      ctx.textAlign = 'left';
      ctx.fillText(item.label, legendX + 18, y + 10);
    });
  }, []);

  return (
    <div className="grid-topology">
      <h2>🔌 Grid Topology Visualization</h2>
      <canvas ref={canvasRef} width={500} height={400} />
      <p className="topology-description">
        Interactive visualization of the power grid network showing substations, transformers, and
        feeders
      </p>
    </div>
  );
};

export default GridTopology;
