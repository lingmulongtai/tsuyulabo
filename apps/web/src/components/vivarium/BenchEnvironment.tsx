import { useEffect, useMemo } from "react";
import { CanvasTexture, SRGBColorSpace } from "three";
import { randomSource } from "./random";

/** Original painted light shapes, not a photographic asset or remote dependency. */
export function BenchEnvironment() {
  const backdrop = useMemo(() => {
    const canvas = document.createElement("canvas"); canvas.width = 1024; canvas.height = 512;
    const c = canvas.getContext("2d")!;
    const wash = c.createLinearGradient(0, 0, 1024, 512);
    wash.addColorStop(0, "#727f7c"); wash.addColorStop(0.45, "#484a3f"); wash.addColorStop(1, "#262e2b");
    c.fillStyle = wash; c.fillRect(0,0,1024,512);
    c.filter = "blur(22px)";
    c.fillStyle = "#a7bcbf"; c.fillRect(680, -30, 190, 340);
    c.fillStyle = "#444f4c"; c.fillRect(756, -30, 14, 360); c.fillRect(670, 125, 220, 15);
    c.fillStyle = "#232c29"; c.fillRect(0,360,1024,45);
    const random = randomSource("bench-lamp");
    for (let i=0;i<7;i++) {
      const x=140+random()*260,y=150+random()*150,r=10+random()*25;
      const g=c.createRadialGradient(x,y,0,x,y,r*2);
      g.addColorStop(0,"#eed09a");g.addColorStop(0.45,"#bb8b50");g.addColorStop(1,"rgba(145,95,43,0)");
      c.fillStyle=g;c.fillRect(x-r*2,y-r*2,r*4,r*4);
    }
    const texture = new CanvasTexture(canvas); texture.colorSpace = SRGBColorSpace; return texture;
  }, []);
  useEffect(() => () => backdrop.dispose(), [backdrop]);
  return <group>
    <mesh position={[0,130,-170]}><planeGeometry args={[680,340]} /><meshBasicMaterial map={backdrop} /></mesh>
    <mesh position={[0,-0.12,0]} rotation={[-Math.PI/2,0,0]} receiveShadow>
      <planeGeometry args={[1800,1800]} /><meshStandardMaterial color="#655e4d" roughness={0.79} />
    </mesh>
  </group>;
}
