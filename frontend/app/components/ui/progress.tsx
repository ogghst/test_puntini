/**
 * Progress Component
 * 
 * A simple progress bar component for displaying completion percentages.
 */

import React from "react";
import { cn } from "@/lib/utils";

interface ProgressProps {
  value: number;
  className?: string;
  max?: number;
}

/**
 * Progress component for displaying completion percentages
 * 
 * @param props - Component props including value, className, and max
 * @returns JSX element representing a progress bar
 */
export const Progress: React.FC<ProgressProps> = ({ 
  value, 
  className, 
  max = 100 
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div 
      className={cn(
        "relative h-2 w-full overflow-hidden rounded-full bg-gray-200",
        className
      )}
    >
      <div
        className="h-full w-full flex-1 bg-blue-600 transition-all duration-300 ease-in-out"
        style={{ transform: `translateX(-${100 - percentage}%)` }}
      />
    </div>
  );
};
