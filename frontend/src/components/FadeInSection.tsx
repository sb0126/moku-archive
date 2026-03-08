"use client";

import React, { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { motion, useInView, useAnimation } from "framer-motion";

interface FadeInSectionProps {
  children: React.ReactNode;
  className?: string;
  delay?: number; // in milliseconds
  direction?: "up" | "down" | "left" | "right" | "none";
}

export function FadeInSection({ children, className, delay = 0, direction = "up" }: FadeInSectionProps) {
  const ref = useRef<HTMLDivElement>(null);
  // framer-motion useInView does not fully support margin with string literal correctly in all setups unless passing to IntersectionObserver API,
  // but we can use an IntersectionObserver or just useInView with margin. 
  // Let's use the provided framer-motion approach. 
  const isInView = useInView(ref, { once: true, amount: 0.1, margin: "0px 0px -100px 0px" });
  const controls = useAnimation();

  useEffect(() => {
    if (isInView) {
      controls.start("visible");
    }
  }, [isInView, controls]);

  const getVariants = () => {
    const distance = 50;
    let x = 0;
    let y = 0;

    switch (direction) {
      case "up": y = distance; break;
      case "down": y = -distance; break;
      case "left": x = distance; break;
      case "right": x = -distance; break;
      case "none": break;
    }

    return {
      hidden: { opacity: 0, x, y },
      visible: { 
        opacity: 1, 
        x: 0, y: 0, 
        transition: { duration: 0.6, ease: "easeOut", delay: delay / 1000 } 
      }
    };
  };

  return (
    <motion.div
      ref={ref}
      variants={getVariants()}
      initial="hidden"
      animate={controls}
      className={cn(className)}
    >
      {children}
    </motion.div>
  );
}
