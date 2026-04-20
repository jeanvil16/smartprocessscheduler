import { Canvas } from "@react-three/fiber";
import gsap from "gsap";
import { useEffect, useMemo, useRef } from "react";

const LANE_Y = {
  express: 1.5,
  standard: 0,
  batch: -1.5,
};

function QueryMonolith({ query }) {
  const meshRef = useRef(null);
  const previousTierRef = useRef(query.tier);
  const previousStatusRef = useRef(query.status);

  useEffect(() => {
    if (!meshRef.current) return;
    const nextTier = query.tier;
    const prevTier = previousTierRef.current;
    const nextStatus = query.status;
    const prevStatus = previousStatusRef.current;

    const tl = gsap.timeline();
    tl.to(meshRef.current.position, {
      y: LANE_Y[nextTier] ?? 0,
      x: nextStatus === "completed" ? 5 : 0,
      duration: 0.7,
      ease: "power2.out",
    });

    const demotionHappened =
      (prevTier === "express" && nextTier !== "express") ||
      (prevTier === "standard" && nextTier === "batch");
    if (demotionHappened && prevStatus !== "completed") {
      tl.to(
        meshRef.current.scale,
        {
          x: 1.25,
          y: 1.25,
          z: 1.25,
          duration: 0.16,
          yoyo: true,
          repeat: 1,
          ease: "power1.inOut",
        },
        0,
      );
      tl.to(
        meshRef.current.rotation,
        {
          z: meshRef.current.rotation.z + 0.25,
          duration: 0.22,
          yoyo: true,
          repeat: 1,
          ease: "power1.inOut",
        },
        0,
      );
    }

    previousTierRef.current = nextTier;
    previousStatusRef.current = nextStatus;
  }, [query.tier, query.status]);

  const color = query.tier === "express" ? "#2D5A27" : query.tier === "standard" ? "#648F52" : "#9AA793";
  return (
    <mesh ref={meshRef} position={[-4, LANE_Y[query.tier] ?? 0, 0]}>
      <boxGeometry args={[0.9, 0.7, 0.7]} />
      <meshStandardMaterial color={color} />
    </mesh>
  );
}

export default function SchedulerScene({ queries }) {
  const lanes = useMemo(
    () => [
      { y: 1.5, label: "Express" },
      { y: 0, label: "Standard" },
      { y: -1.5, label: "Batch" },
    ],
    [],
  );

  return (
    <div className="h-[460px] w-full border-2 border-ink">
      <Canvas camera={{ position: [0, 0, 9], fov: 60 }}>
        <ambientLight intensity={0.7} />
        <directionalLight position={[5, 5, 2]} intensity={1.2} />
        {lanes.map((lane) => (
          <group key={lane.label} position={[0, lane.y, 0]}>
            <mesh>
              <boxGeometry args={[10, 0.08, 1.2]} />
              <meshStandardMaterial color="#1A1A1A" />
            </mesh>
          </group>
        ))}
        {queries.map((query) => (
          <QueryMonolith key={query.query_id} query={query} />
        ))}
      </Canvas>
    </div>
  );
}
