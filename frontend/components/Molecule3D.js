'use client';

import { useEffect, useRef, useState } from 'react';

// Pre-defined 3D coordinates for a realistic chemical structure (e.g., Caffeine-like scaffold)
const ATOMS = [
  { x: -50, y: -50, z: -50, color: '#22c55e', size: 10, element: 'C' }, // Carbon (Green)
  { x: 50, y: -50, z: -50, color: '#22c55e', size: 10, element: 'C' },
  { x: 50, y: 50, z: -50, color: '#22c55e', size: 10, element: 'C' },
  { x: -50, y: 50, z: -50, color: '#22c55e', size: 10, element: 'C' },
  { x: -50, y: -50, z: 50, color: '#22c55e', size: 10, element: 'C' },
  { x: 50, y: -50, z: 50, color: '#00ed64', size: 12, element: 'O' },  // Oxygen (Neon spring green)
  { x: 50, y: 50, z: 50, color: '#22c55e', size: 10, element: 'C' },
  { x: -50, y: 50, z: 50, color: '#00ed64', size: 12, element: 'O' },
  { x: 0, y: -90, z: 0, color: '#06b6d4', size: 9, element: 'N' },     // Nitrogen (Cyan)
  { x: 0, y: 90, z: 0, color: '#06b6d4', size: 9, element: 'N' },
  { x: -90, y: 0, z: 0, color: '#f3f4f6', size: 6, element: 'H' },     // Hydrogen (White/Off-white)
  { x: 90, y: 0, z: 0, color: '#f3f4f6', size: 6, element: 'H' },
];

const BONDS = [
  { from: 0, to: 1 }, { from: 1, to: 2 }, { from: 2, to: 3 }, { from: 3, to: 0 },
  { from: 4, to: 5 }, { from: 5, to: 6 }, { from: 6, to: 7 }, { from: 7, to: 4 },
  { from: 0, to: 4 }, { from: 1, to: 5 }, { from: 2, to: 6 }, { from: 3, to: 7 },
  { from: 0, to: 8 }, { from: 1, to: 8 }, { from: 4, to: 8 },
  { from: 2, to: 9 }, { from: 3, to: 9 }, { from: 6, to: 9 },
  { from: 0, to: 10 }, { from: 4, to: 10 },
  { from: 1, to: 11 }, { from: 5, to: 11 },
];

export default function Molecule3D({ size = 'md', scanning = false, opacity = 1 }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [mouse, setMouse] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  // Rotation angles
  const angleX = useRef(Math.random() * Math.PI);
  const angleY = useRef(Math.random() * Math.PI);

  // Scanning laser position (0 to 100 percentage)
  const scanPos = useRef(0);

  // Parse sizing
  const dimensions = {
    sm: 150,
    md: 260,
    lg: 400,
    xl: 550,
  }[size] || 260;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set pixel density ratio for crisp rendering
    const dpr = window.devicePixelRatio || 1;
    canvas.width = dimensions * dpr;
    canvas.height = dimensions * dpr;
    canvas.style.width = `${dimensions}px`;
    canvas.style.height = `${dimensions}px`;
    ctx.scale(dpr, dpr);

    let animationFrameId;

    // Particle field background dots
    const bgParticles = Array.from({ length: 15 }).map(() => ({
      x: (Math.random() - 0.5) * dimensions * 0.9,
      y: (Math.random() - 0.5) * dimensions * 0.9,
      z: (Math.random() - 0.5) * dimensions * 0.9,
      alpha: Math.random() * 0.5 + 0.2,
    }));

    const render = () => {
      ctx.clearRect(0, 0, dimensions, dimensions);

      // Auto-rotation speed + hover interaction
      const baseSpeedX = 0.003;
      const baseSpeedY = 0.005;
      
      let targetRotX = baseSpeedX;
      let targetRotY = baseSpeedY;

      if (isHovered) {
        // Influence rotation with mouse coordinates
        targetRotX = mouse.y * 0.02;
        targetRotY = mouse.x * 0.02;
      }

      angleX.current += targetRotX;
      angleY.current += targetRotY;

      const cosX = Math.cos(angleX.current);
      const sinX = Math.sin(angleX.current);
      const cosY = Math.cos(angleY.current);
      const sinY = Math.sin(angleY.current);

      const centerX = dimensions / 2;
      const centerY = dimensions / 2;
      const focalLength = dimensions * 1.2;

      // Project particles (background ambient dots)
      bgParticles.forEach((part) => {
        // Rotate X
        let y1 = part.y * cosX - part.z * sinX;
        let z1 = part.z * cosX + part.y * sinX;

        // Rotate Y
        let x2 = part.x * cosY - z1 * sinY;
        let z2 = z1 * cosY + part.x * sinY;

        // Project
        const scale = focalLength / (focalLength + z2);
        const px = centerX + x2 * scale;
        const py = centerY + y1 * scale;

        ctx.beginPath();
        ctx.arc(px, py, 1.2 * scale, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 237, 100, ${part.alpha * scale * 0.45})`;
        ctx.fill();
      });

      // 3D rotation projection helper
      const project = (point) => {
        // Rotate X
        let y1 = point.y * cosX - point.z * sinX;
        let z1 = point.z * cosX + point.y * sinX;

        // Rotate Y
        let x2 = point.x * cosY - z1 * sinY;
        let z2 = z1 * cosY + point.x * sinY;

        // Perspective Projection
        const scale = focalLength / (focalLength + z2);
        const px = centerX + x2 * scale;
        const py = centerY + y1 * scale;

        return { x: px, y: py, z: z2, scale };
      };

      const projectedAtoms = ATOMS.map(project);

      // Draw Bonds (Lines)
      BONDS.forEach((bond) => {
        const from = projectedAtoms[bond.from];
        const to = projectedAtoms[bond.to];

        if (!from || !to) return;

        // Depth sorting alpha
        const avgZ = (from.z + to.z) / 2;
        const alpha = Math.max(0.1, 1 - (avgZ + 100) / 200) * 0.4;

        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);

        // Glowing bond line
        const grad = ctx.createLinearGradient(from.x, from.y, to.x, to.y);
        grad.addColorStop(0, `rgba(0, 237, 100, ${alpha * from.scale})`);
        grad.addColorStop(1, `rgba(6, 182, 212, ${alpha * to.scale})`);

        ctx.strokeStyle = grad;
        ctx.lineWidth = 1.5 * ((from.scale + to.scale) / 2);
        ctx.stroke();
      });

      // Sort atoms by depth (Z-index) so foreground overlaps background
      const sortedIndices = [...Array(ATOMS.length).keys()].sort(
        (a, b) => projectedAtoms[b].z - projectedAtoms[a].z
      );

      // Draw Atoms (Nodes)
      sortedIndices.forEach((idx) => {
        const atom = ATOMS[idx];
        const proj = projectedAtoms[idx];

        // Draw Glow Bloom
        const glowRad = atom.size * 2.8 * proj.scale;
        const radialGrad = ctx.createRadialGradient(
          proj.x, proj.y, 1,
          proj.x, proj.y, glowRad
        );
        radialGrad.addColorStop(0, `${atom.color}55`);
        radialGrad.addColorStop(0.3, `${atom.color}22`);
        radialGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');

        ctx.beginPath();
        ctx.arc(proj.x, proj.y, glowRad, 0, Math.PI * 2);
        ctx.fillStyle = radialGrad;
        ctx.fill();

        // Draw solid core
        ctx.beginPath();
        ctx.arc(proj.x, proj.y, atom.size * 0.5 * proj.scale, 0, Math.PI * 2);
        ctx.fillStyle = atom.color;
        ctx.strokeStyle = '#ffffff55';
        ctx.lineWidth = 0.8 * proj.scale;
        ctx.stroke();
        ctx.fill();
      });

      // ─── Laser Scanning Sweep Overlay ───────────────────────
      if (scanning) {
        scanPos.current = (scanPos.current + 0.8) % 100;
        const scanY = (scanPos.current / 100) * dimensions;

        // Draw scanning laser bar
        const scanGrad = ctx.createLinearGradient(0, scanY - 8, 0, scanY + 8);
        scanGrad.addColorStop(0, 'rgba(0, 237, 100, 0)');
        scanGrad.addColorStop(0.5, 'rgba(0, 237, 100, 0.45)');
        scanGrad.addColorStop(1, 'rgba(0, 237, 100, 0)');

        ctx.fillStyle = scanGrad;
        ctx.fillRect(0, scanY - 8, dimensions, 16);

        // Neon laser core line
        ctx.beginPath();
        ctx.moveTo(0, scanY);
        ctx.lineTo(dimensions, scanY);
        ctx.strokeStyle = 'rgba(0, 237, 100, 0.95)';
        ctx.lineWidth = 1;
        ctx.shadowColor = 'rgba(0, 237, 100, 0.8)';
        ctx.shadowBlur = 10;
        ctx.stroke();
        ctx.shadowBlur = 0; // Reset shadow for next render loop
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [dimensions, isHovered, mouse, scanning]);

  const handleMouseMove = (e) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const cx = rect.width / 2;
    const cy = rect.height / 2;
    // Normalize coordinates -1 to 1
    setMouse({
      x: (e.clientX - rect.left - cx) / cx,
      y: (e.clientY - rect.top - cy) / cy,
    });
  };

  return (
    <div
      ref={containerRef}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onMouseMove={handleMouseMove}
      className="relative flex items-center justify-center select-none"
      style={{
        width: `${dimensions}px`,
        height: `${dimensions}px`,
        opacity: opacity,
      }}
    >
      <canvas ref={canvasRef} className="block pointer-events-none drop-shadow-[0_0_25px_rgba(0,237,100,0.1)]" />
    </div>
  );
}
