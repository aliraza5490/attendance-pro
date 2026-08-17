import React from "react";
import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  subtext?: string;
  icon: LucideIcon;
  trend?: {
    value: string;
    isPositive?: boolean;
  };
  accentColor: "cyan" | "emerald" | "amber" | "indigo" | "rose";
  badge?: string;
  badgeVariant?: "cyan" | "emerald" | "amber" | "indigo" | "rose" | string;
  loading?: boolean;
}

const colorMap = {
  cyan: {
    bgGlow: "from-cyan-500/10 to-transparent",
    borderHover: "hover:border-cyan-500/40",
    iconBg: "bg-cyan-500/15 text-cyan-400 border border-cyan-500/30",
    glow: "glow-cyan",
  },
  emerald: {
    bgGlow: "from-emerald-500/10 to-transparent",
    borderHover: "hover:border-emerald-500/40",
    iconBg: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30",
    glow: "glow-emerald",
  },
  amber: {
    bgGlow: "from-amber-500/10 to-transparent",
    borderHover: "hover:border-amber-500/40",
    iconBg: "bg-amber-500/15 text-amber-400 border border-amber-500/30",
    glow: "",
  },
  indigo: {
    bgGlow: "from-indigo-500/10 to-transparent",
    borderHover: "hover:border-indigo-500/40",
    iconBg: "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30",
    glow: "glow-indigo",
  },
  rose: {
    bgGlow: "from-rose-500/10 to-transparent",
    borderHover: "hover:border-rose-500/40",
    iconBg: "bg-rose-500/15 text-rose-400 border border-rose-500/30",
    glow: "",
  },
};

export function MetricCard({
  title,
  value,
  subtitle,
  subtext,
  icon: Icon,
  trend,
  accentColor,
  badge,
  badgeVariant = "cyan",
  loading,
}: MetricCardProps) {
  const styles = colorMap[accentColor] || colorMap.cyan;
  const description = subtitle || subtext;

  return (
    <div
      className={`glass-panel rounded-2xl p-5 relative overflow-hidden transition-all duration-300 ${styles.borderHover} group`}
    >
      {/* Background soft glow gradient */}
      <div
        className={`absolute inset-0 bg-gradient-to-br ${styles.bgGlow} opacity-60 pointer-events-none group-hover:opacity-100 transition-opacity`}
      />

      <div className="relative z-10 flex items-start justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</p>
            {badge && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-900 border border-slate-700 text-slate-300">
                {badge}
              </span>
            )}
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold tracking-tight text-white font-mono">
              {loading ? "--" : value}
            </span>
            {trend && (
              <span
                className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                  trend.isPositive
                    ? "text-emerald-400 bg-emerald-950/60 border border-emerald-500/30"
                    : "text-amber-400 bg-amber-950/60 border border-amber-500/30"
                }`}
              >
                {trend.value}
              </span>
            )}
          </div>
          {description && (
            <p className="text-[11px] text-slate-400 font-medium">{description}</p>
          )}
        </div>

        <div className={`p-3 rounded-xl ${styles.iconBg} shadow-inner`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}
