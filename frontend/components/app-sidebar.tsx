"use client";

import { useAuth } from "@/contexts/auth-context";
import { Briefcase, LogOut, Search, Settings, User, Zap } from "lucide-react";
import { useRouter } from "next/navigation";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { Badge } from "./ui/badge";

// Menu items for different sections
const prepareItems = [
  {
    title: "Candidate Profile",
    icon: User,
    url: "/dashboard/candidate",
  },
  {
    title: "Search Preferences",
    icon: Settings,
    url: "/dashboard/candidate/search-preferences",
    component: (
      <a href={"/dashboard/candidate/search-preferences"}>
        <Settings />
        <span>{"Search Preferences"}</span>
        <Badge variant={"default"} className="ml-auto">
          Beta
        </Badge>
      </a>
    ),
  },
];

const jobsItems = [
  {
    title: "Job Listings",
    icon: Briefcase,
    url: "/dashboard/job-listings",
  },
];

const applyItems = [
  {
    title: "Auto Apply",
    icon: Zap,
    url: "/dashboard/auto-apply",
    component: (
      <a href={"/dashboard/auto-apply"}>
        <Zap />
        <span>{"Auto Apply"}</span>
        <Badge variant={"default"} className="ml-auto">
          Beta
        </Badge>
      </a>
    ),
  },
];

const adminItems = [
  {
    title: "Companies",
    icon: Briefcase,
    url: "/dashboard/admin/companies",
  },
  {
    title: "Search Company",
    icon: Search,
    url: "/dashboard/admin/companies/search",
  },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const { user, logout, isAdmin } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="border-b border-sidebar-border p-4">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <span className="text-sm font-bold text-primary-foreground">
              void
            </span>
          </div>
          {state === "expanded" && (
            <span className="text-lg font-semibold">AI</span>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>PREPARE</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {prepareItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    {item.component ? (
                      item.component
                    ) : (
                      <a href={item.url}>
                        <item.icon />
                        <span>{item.title}</span>
                      </a>
                    )}
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>JOBS</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {jobsItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <a href={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>APPLY</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {applyItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    isActive={item.url === "/auto-apply"}
                  >
                    {item.component ? (
                      item.component
                    ) : (
                      <a href={item.url}>
                        <item.icon />
                        <span>{item.title}</span>
                      </a>
                    )}
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {isAdmin && (
          <SidebarGroup>
            <SidebarGroupLabel>ADMIN</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {adminItems.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild>
                      <a href={item.url}>
                        <item.icon />
                        <span>{item.title}</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border p-4">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton onClick={handleLogout}>
              <LogOut />
              <span>Logout</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>

        {state === "expanded" && user && (
          <div className="mt-4 flex items-center gap-3 rounded-lg bg-sidebar-accent p-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
              <User className="h-4 w-4" />
            </div>
            <div className="flex flex-col overflow-hidden">
              <span className="truncate text-sm font-medium">
                {user.full_name || "User"}
                {isAdmin && (
                  <span className="ml-2 text-xs text-orange-600">(Admin)</span>
                )}
              </span>
              <span className="truncate text-xs text-muted-foreground">
                {user.email}
              </span>
            </div>
          </div>
        )}
      </SidebarFooter>
    </Sidebar>
  );
}
