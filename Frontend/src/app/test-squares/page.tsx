"use client";

import { Squares } from "@/components/ui/squares-background";

export default function TestSquaresPage() {
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-2xl font-bold mb-8">Squares Background Test</h1>
      
      {/* Test 1: Basic squares */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-4">Test 1: Basic Squares</h2>
        <div className="relative h-[300px] bg-white rounded-lg overflow-hidden border">
          <Squares 
            direction="diagonal"
            speed={1}
            squareSize={40}
            borderColor="#333"
            hoverFillColor="#666"
          />
        </div>
      </div>

      {/* Test 2: Colored squares */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-4">Test 2: Colored Squares</h2>
        <div className="relative h-[300px] bg-white rounded-lg overflow-hidden border">
          <Squares 
            direction="right"
            speed={0.5}
            squareSize={50}
            borderColor="rgba(99, 102, 241, 0.6)"
            hoverFillColor="rgba(99, 102, 241, 0.2)"
          />
        </div>
      </div>

      {/* Test 3: Different directions */}
      <div className="grid grid-cols-2 gap-4 mb-8">
        <div>
          <h3 className="text-md font-semibold mb-2">Up Direction</h3>
          <div className="relative h-[200px] bg-white rounded-lg overflow-hidden border">
            <Squares 
              direction="up"
              speed={0.8}
              squareSize={30}
              borderColor="rgba(34, 197, 94, 0.5)"
              hoverFillColor="rgba(34, 197, 94, 0.1)"
            />
          </div>
        </div>
        <div>
          <h3 className="text-md font-semibold mb-2">Down Direction</h3>
          <div className="relative h-[200px] bg-white rounded-lg overflow-hidden border">
            <Squares 
              direction="down"
              speed={0.8}
              squareSize={30}
              borderColor="rgba(239, 68, 68, 0.5)"
              hoverFillColor="rgba(239, 68, 68, 0.1)"
            />
          </div>
        </div>
      </div>

      {/* Test 4: Full page background */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Test 4: Full Page Background</h2>
        <div className="relative h-[400px] bg-white rounded-lg overflow-hidden border">
          <Squares 
            direction="diagonal"
            speed={0.3}
            squareSize={60}
            borderColor="rgba(99, 102, 241, 0.4)"
            hoverFillColor="rgba(99, 102, 241, 0.15)"
            className="opacity-70"
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="bg-white/80 backdrop-blur-sm p-8 rounded-lg shadow-lg">
              <h3 className="text-xl font-bold mb-2">Content Over Squares</h3>
              <p className="text-gray-600">This content should be visible over the animated squares background.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
