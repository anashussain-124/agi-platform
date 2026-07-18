"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * NeuralMesh — the signature 3D moment.
 * A lattice of nodes arranged on a sphere (a "cortex"). Edges between near
 * neighbours glow; pulses travel along edges. Scroll velocity and cursor
 * proximity increase firing rate. Degrades to nothing when the user prefers
 * reduced motion (canvas is hidden via CSS) — no JS runs.
 */
export default function NeuralMesh() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;

    const mount = mountRef.current;
    if (!mount) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      55,
      mount.clientWidth / mount.clientHeight,
      0.1,
      100
    );
    camera.position.z = 14;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    mount.appendChild(renderer.domElement);
    renderer.domElement.style.display = "block";

    // ── build nodes on a fibonacci sphere ──
    const N = 220;
    const R = 6;
    const positions = new Float32Array(N * 3);
    const nodes: THREE.Vector3[] = [];
    const golden = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < N; i++) {
      const y = 1 - (i / (N - 1)) * 2;
      const r = Math.sqrt(1 - y * y);
      const theta = golden * i;
      const v = new THREE.Vector3(
        Math.cos(theta) * r,
        y,
        Math.sin(theta) * r
      ).multiplyScalar(R);
      nodes.push(v);
      positions[i * 3] = v.x;
      positions[i * 3 + 1] = v.y;
      positions[i * 3 + 2] = v.z;
    }

    const nodeGeo = new THREE.BufferGeometry();
    nodeGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const nodeMat = new THREE.PointsMaterial({
      color: 0xffb347,
      size: 0.13,
      transparent: true,
      opacity: 0.9,
      sizeAttenuation: true,
    });
    const points = new THREE.Points(nodeGeo, nodeMat);
    scene.add(points);

    // ── edges between near neighbours ──
    const edgeList: [number, number][] = [];
    const maxDist = 2.4;
    for (let i = 0; i < N; i++) {
      for (let j = i + 1; j < N; j++) {
        if (nodes[i].distanceTo(nodes[j]) < maxDist) {
          edgeList.push([i, j]);
        }
      }
    }
    const edgePos = new Float32Array(edgeList.length * 6);
    edgeList.forEach(([a, b], k) => {
      const va = nodes[a], vb = nodes[b];
      edgePos[k * 6] = va.x; edgePos[k * 6 + 1] = va.y; edgePos[k * 6 + 2] = va.z;
      edgePos[k * 6 + 3] = vb.x; edgePos[k * 6 + 4] = vb.y; edgePos[k * 6 + 5] = vb.z;
    });
    const edgeGeo = new THREE.BufferGeometry();
    edgeGeo.setAttribute("position", new THREE.BufferAttribute(edgePos, 3));
    const edgeMat = new THREE.LineBasicMaterial({
      color: 0x8b7bf0,
      transparent: true,
      opacity: 0.12,
    });
    const lines = new THREE.LineSegments(edgeGeo, edgeMat);
    scene.add(lines);

    // ── travelling pulses (signal along edges) ──
    const PULSES = 60;
    const pulsePos = new Float32Array(PULSES * 3);
    const pulseGeo = new THREE.BufferGeometry();
    pulseGeo.setAttribute("position", new THREE.BufferAttribute(pulsePos, 3));
    const pulseMat = new THREE.PointsMaterial({
      color: 0xffd9a0,
      size: 0.22,
      transparent: true,
      opacity: 0.95,
      sizeAttenuation: true,
    });
    const pulses = new THREE.Points(pulseGeo, pulseMat);
    scene.add(pulses);

    const pulseState = Array.from({ length: PULSES }, () => ({
      edge: Math.floor(Math.random() * edgeList.length),
      t: Math.random(),
      speed: 0.004 + Math.random() * 0.01,
    }));

    // ── interaction state ──
    let scrollVel = 0;
    let targetRotX = 0, targetRotY = 0;
    let mouseX = 0, mouseY = 0;
    const onScroll = () => {
      scrollVel = Math.min(scrollVel + 0.06, 1);
    };
    const onMove = (e: MouseEvent) => {
      mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
      mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("mousemove", onMove);

    let raf = 0;
    let startT = performance.now();

    const animate = () => {
      const t = (performance.now() - startT) / 1000;

      // rotation follows cursor, eased
      targetRotY = mouseX * 0.3;
      targetRotX = mouseY * 0.2;
      points.rotation.y += (targetRotY - points.rotation.y) * 0.04 + 0.0015;
      points.rotation.x += (targetRotX - points.rotation.x) * 0.04;
      lines.rotation.copy(points.rotation);
      pulses.rotation.copy(points.rotation);

      // edge opacity breathes with scroll velocity
      edgeMat.opacity = 0.1 + scrollVel * 0.4;
      scrollVel *= 0.96;

      // advance pulses
      for (let p = 0; p < PULSES; p++) {
        const st = pulseState[p];
        st.t += st.speed * (1 + scrollVel * 3);
        if (st.t >= 1) {
          st.t = 0;
          st.edge = Math.floor(Math.random() * edgeList.length);
        }
        const [a, b] = edgeList[st.edge];
        const va = nodes[a], vb = nodes[b];
        const x = va.x + (vb.x - va.x) * st.t;
        const y = va.y + (vb.y - va.y) * st.t;
        const z = va.z + (vb.z - va.z) * st.t;
        pulsePos[p * 3] = x;
        pulsePos[p * 3 + 1] = y;
        pulsePos[p * 3 + 2] = z;
      }
      pulseGeo.attributes.position.needsUpdate = true;
      // fade pulses in/out slightly for life
      pulseMat.opacity = 0.7 + Math.sin(t * 2) * 0.2;

      renderer.render(scene, camera);
      raf = requestAnimationFrame(animate);
    };
    animate();

    const onResize = () => {
      if (!mount) return;
      camera.aspect = mount.clientWidth / mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      nodeGeo.dispose();
      edgeGeo.dispose();
      pulseGeo.dispose();
      if (renderer.domElement.parentNode === mount) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div
      ref={mountRef}
      id="mesh-canvas"
      aria-hidden="true"
      className="absolute inset-0 -z-10"
    />
  );
}
