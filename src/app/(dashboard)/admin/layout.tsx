"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

const adminNavigation = [
  { name: "Overview", href: "/admin" },
  { name: "Users", href: "/admin/users" },
  { name: "Cameras", href: "/admin/cameras" },
  { name: "Settings", href: "/admin/settings" },
  { name: "Logs", href: "/admin/logs" },
]

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()

  return (
    <div className="space-y-6">
      <div className="border-b">
        <div className="flex h-16 items-center px-4">
          <h1 className="text-2xl font-bold">Admin Panel</h1>
        </div>
        <nav className="flex overflow-x-auto px-4">
          {adminNavigation.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "border-b-2 px-4 py-3 text-sm font-medium",
                pathname === item.href
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              {item.name}
            </Link>
          ))}
        </nav>
      </div>
      {children}
    </div>
  )
} 