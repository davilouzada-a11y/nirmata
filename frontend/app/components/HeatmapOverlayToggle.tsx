"use client";

interface Props {
  enabled: boolean;
  opacity: number;
  onToggle: (v: boolean) => void;
  onOpacity: (v: number) => void;
  disabled?: boolean;
}

export default function HeatmapOverlayToggle({ enabled, opacity, onToggle, onOpacity, disabled }: Props) {
  return (
    <div className="rx-panel flex flex-wrap items-center gap-3 px-3 py-2 text-xs font-bold text-white/55">
      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={enabled}
          disabled={disabled}
          onChange={(e) => onToggle(e.target.checked)}
        />
        Mostrar heatmap (Grad-CAM)
      </label>
      <label className="flex items-center gap-2">
        Opacidade
        <input
          type="range" min={0} max={1} step={0.05} value={opacity}
          disabled={!enabled || disabled}
          onChange={(e) => onOpacity(Number(e.target.value))}
        />
      </label>
    </div>
  );
}
