<script lang="ts">
    import { onMount } from "svelte";
    import {
        HOTSPOTS,
        CONFLICT_ZONES,
        CHOKEPOINTS,
        CABLE_LANDINGS,
        NUCLEAR_SITES,
        MILITARY_BASES,
        OCEANS,
        SANCTIONED_COUNTRY_IDS,
        THREAT_COLORS,
        WEATHER_CODES,
    } from "$lib/config/map";

    let mapContainer: HTMLDivElement;
    let d3Module: typeof import("d3") | null = null;
    let svg: any = null;
    let mapGroup: any = null;
    let projection: any = null;
    let path: any = null;
    let zoom: any = null;

    const WIDTH = 800;
    const HEIGHT = 400;

    // Tooltip state
    let tooltipContent = $state<{
        title: string;
        color: string;
        lines: string[];
    } | null>(null);
    let tooltipPosition = $state({ left: 0, top: 0 });
    let tooltipVisible = $state(false);

    // Get local time at longitude
    function getLocalTime(lon: number): string {
        const now = new Date();
        const utcHours = now.getUTCHours();
        const utcMinutes = now.getUTCMinutes();
        const offsetHours = Math.round(lon / 15);
        let localHours = (utcHours + offsetHours + 24) % 24;
        const ampm = localHours >= 12 ? "PM" : "AM";
        localHours = localHours % 12 || 12;
        return `${localHours}:${utcMinutes.toString().padStart(2, "0")} ${ampm}`;
    }

    // Enable zoom/pan behavior on the map
    function enableZoom(): void {
        if (!svg || !zoom) return;
        svg.call(zoom);
    }

    // Calculate day/night terminator points
    function calculateTerminator(): [number, number][] {
        const now = new Date();
        const dayOfYear = Math.floor(
            (now.getTime() - new Date(now.getFullYear(), 0, 0).getTime()) /
                86400000,
        );
        const declination =
            -23.45 * Math.cos(((360 / 365) * (dayOfYear + 10) * Math.PI) / 180);
        const hourAngle =
            (now.getUTCHours() + now.getUTCMinutes() / 60) * 15 - 180;

        const terminatorPoints: [number, number][] = [];
        for (let lat = -90; lat <= 90; lat += 2) {
            const tanDec = Math.tan((declination * Math.PI) / 180);
            const tanLat = Math.tan((lat * Math.PI) / 180);
            let lon =
                -hourAngle + (Math.acos(-tanDec * tanLat) * 180) / Math.PI;
            if (isNaN(lon))
                lon = lat * declination > 0 ? -hourAngle + 180 : -hourAngle;
            terminatorPoints.push([lon, lat]);
        }
        for (let lat = 90; lat >= -90; lat -= 2) {
            const tanDec = Math.tan((declination * Math.PI) / 180);
            const tanLat = Math.tan((lat * Math.PI) / 180);
            let lon =
                -hourAngle - (Math.acos(-tanDec * tanLat) * 180) / Math.PI;
            if (isNaN(lon))
                lon = lat * declination > 0 ? -hourAngle - 180 : -hourAngle;
            terminatorPoints.push([lon, lat]);
        }
        return terminatorPoints;
    }

    // Show tooltip using state (safe rendering)
    function showTooltip(
        event: MouseEvent,
        title: string,
        color: string,
        lines: string[] = [],
    ): void {
        if (!mapContainer) return;
        const rect = mapContainer.getBoundingClientRect();
        tooltipContent = { title, color, lines };
        tooltipPosition = {
            left: event.clientX - rect.left + 15,
            top: event.clientY - rect.top - 10,
        };
        tooltipVisible = true;
    }

    // Move tooltip
    function moveTooltip(event: MouseEvent): void {
        if (!mapContainer) return;
        const rect = mapContainer.getBoundingClientRect();
        tooltipPosition = {
            left: event.clientX - rect.left + 15,
            top: event.clientY - rect.top - 10,
        };
    }

    // Hide tooltip
    function hideTooltip(): void {
        tooltipVisible = false;
        tooltipContent = null;
    }

    // Build enhanced tooltip with weather
    async function showEnhancedTooltip(
        event: MouseEvent,
        _name: string,
        lat: number,
        lon: number,
        desc: string,
        color: string,
    ): Promise<void> {
        const localTime = getLocalTime(lon);
        const lines = [`🕐 Local: ${localTime}`];
        showTooltip(event, desc, color, lines);
    }

    // Initialize map
    async function initMap(): Promise<void> {
        const d3 = await import("d3");
        d3Module = d3;
        const topojson = await import("topojson-client");

        const svgEl = mapContainer.querySelector("svg");
        if (!svgEl) return;

        svg = d3.select(svgEl);
        svg.attr("viewBox", `0 0 ${WIDTH} ${HEIGHT}`);

        mapGroup = svg.append("g").attr("id", "mapGroup");

        // Setup zoom - disable scroll wheel, allow touch pinch and buttons
        zoom = d3
            .zoom<SVGSVGElement, unknown>()
            .scaleExtent([1, 6])
            .filter((event) => {
                // Block scroll wheel zoom (wheel events)
                if (event.type === "wheel") return false;
                // Allow touch events (pinch zoom on mobile)
                if (event.type.startsWith("touch")) return true;
                // Allow mouse drag for panning
                if (event.type === "mousedown" || event.type === "mousemove")
                    return true;
                // Block double-click zoom
                if (event.type === "dblclick") return false;
                // Allow other events (programmatic zoom from buttons)
                return true;
            })
            .on("zoom", (event) => {
                mapGroup.attr("transform", event.transform.toString());
            });

        enableZoom();

        // Setup projection
        projection = d3
            .geoEquirectangular()
            .scale(130)
            .center([0, 20])
            .translate([WIDTH / 2, HEIGHT / 2 - 30]);

        path = d3.geoPath().projection(projection);

        // Load world data
        try {
            const response = await fetch(
                "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json",
            );
            const world = await response.json();
            const countries = topojson.feature(
                world,
                world.objects.countries as any,
            ) as unknown as GeoJSON.FeatureCollection;

            // Draw countries
            mapGroup
                .selectAll("path.country")
                .data(countries.features)
                .enter()
                .append("path")
                .attr("class", "country")
                .attr("d", path as unknown as string)
                .attr("fill", (d: GeoJSON.Feature) =>
                    SANCTIONED_COUNTRY_IDS.includes(+(d.id || 0))
                        ? "#2a1a1a"
                        : "#0f3028",
                )
                .attr("stroke", (d: GeoJSON.Feature) =>
                    SANCTIONED_COUNTRY_IDS.includes(+(d.id || 0))
                        ? "#4a2020"
                        : "#1a5040",
                )
                .attr("stroke-width", 0.5);

            // Draw graticule
            const graticule = d3.geoGraticule().step([30, 30]);
            mapGroup
                .append("path")
                .datum(graticule)
                .attr("d", path as unknown as string)
                .attr("fill", "none")
                .attr("stroke", "#1a3830")
                .attr("stroke-width", 0.3)
                .attr("stroke-dasharray", "2,2");

            // Draw ocean labels
            OCEANS.forEach((o) => {
                const [x, y] = projection([o.lon, o.lat]) || [0, 0];
                if (x && y) {
                    mapGroup
                        .append("text")
                        .attr("x", x)
                        .attr("y", y)
                        .attr("fill", "#1a4a40")
                        .attr("font-size", "10px")
                        .attr("font-family", "monospace")
                        .attr("text-anchor", "middle")
                        .attr("opacity", 0.6)
                        .text(o.name);
                }
            });

            // Draw day/night terminator
            const terminatorPoints = calculateTerminator();
            mapGroup
                .append("path")
                .datum({
                    type: "Polygon",
                    coordinates: [terminatorPoints],
                } as GeoJSON.Polygon)
                .attr("d", path as unknown as string)
                .attr("fill", "rgba(0,0,0,0.3)")
                .attr("stroke", "none");

            // Draw conflict zones
            CONFLICT_ZONES.forEach((zone) => {
                mapGroup
                    .append("path")
                    .datum({
                        type: "Polygon",
                        coordinates: [zone.coords],
                    } as GeoJSON.Polygon)
                    .attr("d", path as unknown as string)
                    .attr("fill", zone.color)
                    .attr("fill-opacity", 0.15)
                    .attr("stroke", zone.color)
                    .attr("stroke-width", 0.5)
                    .attr("stroke-opacity", 0.4);
            });

            // Draw hotspots
            HOTSPOTS.forEach((h) => {
                const [x, y] = projection([h.lon, h.lat]) || [0, 0];
                if (x && y) {
                    const color = THREAT_COLORS[h.level];
                    // Pulsing circle
                    mapGroup
                        .append("circle")
                        .attr("cx", x)
                        .attr("cy", y)
                        .attr("r", 6)
                        .attr("fill", color)
                        .attr("fill-opacity", 0.3)
                        .attr("class", "pulse");
                    // Inner dot
                    mapGroup
                        .append("circle")
                        .attr("cx", x)
                        .attr("cy", y)
                        .attr("r", 3)
                        .attr("fill", color);
                    // Label
                    mapGroup
                        .append("text")
                        .attr("x", x + 8)
                        .attr("y", y + 3)
                        .attr("fill", color)
                        .attr("font-size", "8px")
                        .attr("font-family", "monospace")
                        .text(h.name);
                    // Hit area
                    mapGroup
                        .append("circle")
                        .attr("cx", x)
                        .attr("cy", y)
                        .attr("r", 12)
                        .attr("fill", "transparent")
                        .attr("class", "hotspot-hit")
                        .on("mouseenter", (event: MouseEvent) =>
                            showEnhancedTooltip(
                                event,
                                h.name,
                                h.lat,
                                h.lon,
                                h.desc,
                                color,
                            ),
                        )
                        .on("mousemove", moveTooltip)
                        .on("mouseleave", hideTooltip);
                }
            });
        } catch (err) {
            console.error("Failed to load map data:", err);
        }
    }

    // Zoom controls
    function zoomIn(): void {
        if (!svg || !zoom) return;
        svg.transition().duration(300).call(zoom.scaleBy, 1.5);
    }

    function zoomOut(): void {
        if (!svg || !zoom) return;
        svg.transition()
            .duration(300)
            .call(zoom.scaleBy, 1 / 1.5);
    }

    function resetZoom(): void {
        if (!svg || !zoom || !d3Module) return;
        svg.transition()
            .duration(300)
            .call(zoom.transform, d3Module.zoomIdentity);
    }

    onMount(() => {
        initMap();
    });
</script>

<div
    class="h-full flex flex-col border border-neutral-800 bg-neutral-900 rounded-xl overflow-hidden shadow-sm shadow-neutral-950"
>
    <div
        class="bg-neutral-800/80 px-4 py-2 border-b border-neutral-800 flex items-center justify-between"
    >
        <h3
            class="text-xs font-bold uppercase tracking-wider text-neutral-300 flex items-center gap-2"
        >
            <div
                class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"
            ></div>
            Global Map
        </h3>
    </div>

    <div class="map-container flex-1 bg-neutral-950" bind:this={mapContainer}>
        <svg class="map-svg w-full h-full"></svg>
        {#if tooltipVisible && tooltipContent}
            <div
                class="map-tooltip z-50 absolute bg-neutral-950 border border-neutral-800 rounded p-2 text-xs max-w-[250px] pointer-events-none"
                style="left: {tooltipPosition.left}px; top: {tooltipPosition.top}px;"
            >
                <strong style="color: {tooltipContent.color}"
                    >{tooltipContent.title}</strong
                >
                {#each tooltipContent.lines as line}
                    <br /><span class="tooltip-line text-neutral-400"
                        >{line}</span
                    >
                {/each}
            </div>
        {/if}
        <div
            class="zoom-controls absolute bottom-2 right-2 flex flex-col gap-1"
        >
            <button
                class="w-8 h-8 flex items-center justify-center bg-neutral-900/90 border border-neutral-700 rounded text-neutral-400 hover:text-white hover:bg-neutral-800 transition"
                onclick={zoomIn}
                title="Zoom in">+</button
            >
            <button
                class="w-8 h-8 flex items-center justify-center bg-neutral-900/90 border border-neutral-700 rounded text-neutral-400 hover:text-white hover:bg-neutral-800 transition"
                onclick={zoomOut}
                title="Zoom out">−</button
            >
            <button
                class="w-8 h-8 flex items-center justify-center bg-neutral-900/90 border border-neutral-700 rounded text-neutral-400 hover:text-white hover:bg-neutral-800 transition"
                onclick={resetZoom}
                title="Reset">⟲</button
            >
        </div>
        <div
            class="map-legend absolute top-2 right-2 flex flex-col gap-1 bg-neutral-900/90 p-2 rounded border border-neutral-800 text-[10px] text-neutral-400"
        >
            <div class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-red-500"></span> Critical
            </div>
            <div class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-[#ffcc00]"></span> Elevated
            </div>
            <div class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-[#00ff88]"></span> Monitoring
            </div>
        </div>
    </div>
</div>

<style>
    .map-container {
        position: relative;
        min-height: 350px;
    }

    /* Pulse animation for hotspots */
    :global(.pulse) {
        animation: pulse 2s ease-in-out infinite;
    }

    @keyframes pulse {
        0%,
        100% {
            r: 6;
            opacity: 0.3;
        }
        50% {
            r: 10;
            opacity: 0.1;
        }
    }

    :global(.hotspot-hit) {
        cursor: pointer;
    }
</style>
