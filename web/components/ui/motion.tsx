"use client";
import { motion, AnimatePresence } from "framer-motion";
import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

type MotionButtonProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "onDrag" | "onDragStart" | "onDragEnd" | "onAnimationStart" | "onAnimationEnd">;
type MotionCardProps = Omit<HTMLAttributes<HTMLDivElement>, "onDrag" | "onDragStart" | "onDragEnd" | "onAnimationStart" | "onAnimationEnd">;

export function AnimatedButton({ children, className, ...props }: MotionButtonProps) {
  return <motion.button whileHover={{ y: -2, scale: 1.01 }} whileTap={{ scale: .98 }} transition={{ type: "spring", stiffness: 420, damping: 24 }} className={cn("motion-button", className)} {...props}>{children}</motion.button>;
}
export function AnimatedCard({ children, className, ...props }: MotionCardProps) {
  return <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} whileHover={{ y: -3 }} transition={{ duration: .22 }} className={cn("motion-card", className)} {...props}>{children}</motion.div>;
}
export function AnimatedReveal({ children, className }: { children: ReactNode; className?: string }) {
  return <AnimatePresence mode="wait"><motion.div key="reveal" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -5 }} transition={{ duration: .2 }} className={className}>{children}</motion.div></AnimatePresence>;
}
export function StatusBadge({ children, tone = "success" }: { children: ReactNode; tone?: "success" | "warning" | "neutral" | "info" }) {
  return <span className={`status-badge status-badge-${tone}`}><i aria-hidden="true" />{children}</span>;
}
