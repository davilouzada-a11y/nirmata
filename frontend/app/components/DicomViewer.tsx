"use client";

/**
 * Radiograph viewer with optional Grad-CAM heatmap overlay.
 *
 * - PNG/JPG studies render directly via <img> with CSS window/contrast controls.
 * - True DICOM studies render with DWV (https://github.com/ivmartel/dwv), loaded
 *   dynamically so it never runs during SSR/build. DWV fetches the protected
 *   /image endpoint with the bearer token via request headers.
 *
 * The heatmap is an absolutely-positioned layer over whichever base renderer is
 * active, with opacity driven by the parent.
 */
import { useEffect, useRef, useState } from "react";
import { getToken } from "../lib/api";

interface Props {
  imageUrl: string;
  isDicom: boolean;
  heatmapUrl: string | null;
  showHeatmap: boolean;
  heatmapOpacity: number;
}

const LAYER_GROUP_ID = "dwv-layer-group";

export default function DicomViewer({ imageUrl, isDicom, heatmapUrl, showHeatmap, heatmapOpacity }: Props) {
  const [contrast, setContrast] = useState(100);
  const [brightness, setBrightness] = useState(100);
  const [dicomError, setDicomError] = useState<string | null>(null);
  const dwvRef = useRef<any>(null);

  useEffect(() => {
    if (!isDicom) return;
    let app: any;
    let cancelled = false;

    (async () => {
      try {
        const dwv = await import("dwv");
        app = new dwv.App();
        app.init({
          dataViewConfigs: { "*": [{ divId: LAYER_GROUP_ID }] },
        });
        const token = getToken();
        const headers = token ? [{ name: "Authorization", value: `Bearer ${token}` }] : [];
        if (!cancelled) {
          app.loadURLs([imageUrl], { requestHeaders: headers });
          dwvRef.current = app;
        }
      } catch (err) {
        if (!cancelled) setDicomError("Falha ao carregar DICOM com DWV — verifique o arquivo.");
      }
    })();

    return () => {
      cancelled = true;
      try { app?.reset?.(); } catch { /* noop */ }
    };
  }, [isDicom, imageUrl]);

  return (
    <div className="space-y-2">
      <div className="relative aspect-square w-full overflow-hidden rounded-xl border border-slate-800 bg-black">
        {isDicom ? (
          <div
            id={LAYER_GROUP_ID}
            className="absolute inset-0 h-full w-full"
            style={{ filter: `contrast(${contrast}%) brightness(${brightness}%)` }}
          />
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={imageUrl}
            alt="Radiografia"
            className="absolute inset-0 h-full w-full object-contain"
            style={{ filter: `contrast(${contrast}%) brightness(${brightness}%)` }}
          />
        )}

        {showHeatmap && heatmapUrl && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={heatmapUrl}
            alt="Heatmap"
            className="pointer-events-none absolute inset-0 h-full w-full object-contain mix-blend-screen"
            style={{ opacity: heatmapOpacity }}
          />
        )}

        {dicomError && (
          <p className="absolute inset-x-0 bottom-0 bg-black/70 p-2 text-center text-xs text-critical">
            {dicomError}
          </p>
        )}
      </div>

      <div className="flex gap-4 text-xs text-slate-400">
        <label className="flex items-center gap-2">
          Contraste
          <input type="range" min={50} max={200} value={contrast}
            onChange={(e) => setContrast(Number(e.target.value))} />
        </label>
        <label className="flex items-center gap-2">
          Brilho
          <input type="range" min={50} max={200} value={brightness}
            onChange={(e) => setBrightness(Number(e.target.value))} />
        </label>
      </div>
    </div>
  );
}
