import React, { useEffect, useRef } from "react";
import * as THREE from "three";

interface VolumeRendererProps {
  volumeData: Uint8Array; // Raw texture data
  dimensions: [number, number, number];
}

export const VolumeRenderer: React.FC<VolumeRendererProps> = ({
  volumeData,
  dimensions,
}) => {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mountRef.current) return;

    // 1. Scene Setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);

    const camera = new THREE.PerspectiveCamera(
      75,
      mountRef.current.clientWidth / mountRef.current.clientHeight,
      0.1,
      1000
    );
    camera.position.z = 2;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(
      mountRef.current.clientWidth,
      mountRef.current.clientHeight
    );
    mountRef.current.appendChild(renderer.domElement);

    // 2. Texture Generation (3D)
    const texture = new THREE.Data3DTexture(
      volumeData,
      dimensions[0],
      dimensions[1],
      dimensions[2]
    );
    texture.format = THREE.RedFormat;
    texture.minFilter = THREE.LinearFilter;
    texture.magFilter = THREE.LinearFilter;
    texture.unpackAlignment = 1;
    texture.needsUpdate = true;

    // 3. Shader (Raymarching)
    // Simplified shader for demo
    const geometry = new THREE.BoxGeometry(1, 1, 1);
    const material = new THREE.ShaderMaterial({
      uniforms: {
        uVolume: { value: texture },
        uThreshold: { value: 0.15 },
      },
      vertexShader: `
           varying vec3 vOrigin;
           varying vec3 vDirection;
           void main() {
               vOrigin = vec3(viewMatrix * modelMatrix * vec4(position, 1.0)).xyz;
               vDirection = position - cameraPosition; 
               gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
           }
       `,
      fragmentShader: `
           precision highp float;
           precision highp int;
           precision highp sampler3D;

           uniform sampler3D uVolume;
           uniform float uThreshold;
           
           varying vec3 vOrigin;
           
           void main() {
               vec3 color = vec3(1.0, 0.0, 0.0); // Placeholder
               gl_FragColor = vec4(color, 0.1); 
               // Full raymarching loop omitted for brevity in prototype
               // Typically involves stepping through uVolume
           }
       `,
      side: THREE.BackSide,
      transparent: true,
    });

    const cube = new THREE.Mesh(geometry, material);
    scene.add(cube);

    // 4. Loop
    let frameId = 0;
    const animate = () => {
      frameId = requestAnimationFrame(animate);
      cube.rotation.x += 0.01;
      cube.rotation.y += 0.01;
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(frameId);
      if (mountRef.current) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [volumeData]);

  return <div ref={mountRef} className="w-full h-full" />;
};
