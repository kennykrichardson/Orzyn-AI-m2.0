import { Canvas, useFrame } from "@react-three/fiber";
import { Float, Sparkles } from "@react-three/drei";
import { useMemo, useRef } from "react";
import type { Points } from "three";
import * as THREE from "three";
import { useReducedMotionPreference } from "../hooks/useReducedMotion";

function StarMesh({ count }: { count: number }) {
  const ref = useRef<Points>(null);
  const positions = useMemo(() => {
    const buffer = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      buffer[i * 3] = (Math.random() - 0.5) * 16;
      buffer[i * 3 + 1] = (Math.random() - 0.5) * 9;
      buffer[i * 3 + 2] = (Math.random() - 0.5) * 7;
    }
    return buffer;
  }, [count]);

  useFrame((state) => {
    if (!ref.current) return;
    ref.current.rotation.y = state.clock.elapsedTime * 0.018;
    ref.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.12) * 0.025;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color="#ff1a1a" size={0.015} transparent opacity={0.62} blending={THREE.AdditiveBlending} />
    </points>
  );
}

export function RedMoon() {
  return (
    <Float speed={0.55} rotationIntensity={0.18} floatIntensity={0.22}>
      <mesh position={[2.75, 0.7, -2.2]}>
        <sphereGeometry args={[1.65, 64, 64]} />
        <meshStandardMaterial color="#b60000" emissive="#ff1010" emissiveIntensity={1.15} roughness={0.9} />
      </mesh>
      <mesh position={[2.72, 0.66, -2.18]}>
        <sphereGeometry args={[1.68, 64, 64]} />
        <meshBasicMaterial color="#ff1a1a" wireframe transparent opacity={0.08} />
      </mesh>
    </Float>
  );
}

export function ParticleField() {
  const reduced = useReducedMotionPreference();

  return (
    <div className="webgl-layer absolute inset-0 pointer-events-none" aria-hidden="true">
      <Canvas dpr={[1, 1.5]} camera={{ position: [0, 0, 5.5], fov: 52 }} gl={{ antialias: false, alpha: true }}>
        <ambientLight intensity={0.55} />
        <pointLight position={[4, 2, 3]} color="#ff1a1a" intensity={3.5} />
        <StarMesh count={reduced ? 260 : 950} />
        <Sparkles count={reduced ? 40 : 120} scale={[8, 4.5, 3]} size={1.1} speed={reduced ? 0.05 : 0.32} color="#ff1a1a" />
        {/* <RedMoon /> */}
      </Canvas>
    </div>
  );
}
