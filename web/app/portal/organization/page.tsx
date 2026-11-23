"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
export default function OrganizationRedirectPage(){
 const {user,loading}=useAuth(); const router=useRouter();
 useEffect(()=>{if(loading)return;if(user?.role!=="admin"){router.replace("/portal");return;}fetch("/api/backend/api/v1/clinic/me/organization",{cache:"no-store"}).then(async r=>{const data=await r.json();if(!r.ok)throw new Error(data.detail||"No organization assigned");router.replace("/portal/super-admin/"+data.id);}).catch(()=>router.replace("/portal/manage/team"));},[user,loading,router]);
 return <main className="min-h-screen p-10 text-sm text-slate-500">Opening your organization workspace…</main>;
}
