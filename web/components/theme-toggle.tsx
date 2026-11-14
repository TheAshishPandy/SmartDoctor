"use client";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
export function ThemeToggle() {
  const {resolvedTheme,setTheme}=useTheme(); const [ready,setReady]=useState(false);
  useEffect(()=>setReady(true),[]);
  const dark=resolvedTheme==="dark";
  return <button className="icon-button" onClick={()=>setTheme(dark?"light":"dark")} aria-label="Toggle color theme" title="Toggle theme">{ready&&dark?<Sun size={17}/>:<Moon size={17}/>}</button>;
}