"""
Tire Pressure Calculation Engine for Modern Road Bikes.
Calibrated against Silca impedance breakpoint research and SRAM AXS tire pressure models:
- Dynamic road weight distribution in hood cruising position: Front ~45%, Rear ~55%
- Front tire includes dynamic impact & braking margin (~0.92 of rear pressure, 5-7 PSI lower)
- Casing formula: P_rear ≈ (TotalSysWeight_kg * 105.0) / (Width_mm^1.45)
- Tubeless reduction factor: 0.92 (-8%)
- ISO/ETRTO Hookless limit strictly monitored at 72.5 PSI (5.0 Bar)
"""
from typing import Dict, Any


def calculate_tire_pressure(
    rider_weight_kg: float,
    width_mm: float,
    bike_weight_kg: float = 8.5,
    is_tubeless: bool = False,
    is_wet_rough: bool = False,
    lang: str = "zh_hant"
) -> Dict[str, Any]:
    """Calculate recommended front and rear tire pressure."""
    rider_w = max(40.0, min(140.0, float(rider_weight_kg)))
    w_mm = max(23.0, min(38.0, float(width_mm)))
    bike_w = max(5.0, min(20.0, float(bike_weight_kg)))
    total_sys_kg = rider_w + bike_w

    # Rear wheel baseline calibrated for modern road asphalt (Silca impedance breakpoint model, K=105)
    rear_base = (total_sys_kg * 105.0) / (w_mm ** 1.45)
    # Front wheel carries ~45% static weight + dynamic braking/impact margin -> 0.92 of rear
    front_base = rear_base * 0.92

    # Surface condition factor (rough pavement / wet grip reduction: -10%)
    surface_factor = 0.90 if is_wet_rough else 1.0

    # Tube vs Tubeless factor (tubeless allows ~8% lower pressure for equivalent rolling resistance and suppleness)
    tube_factor = 0.92 if is_tubeless else 1.0

    front_psi = round(front_base * surface_factor * tube_factor)
    rear_psi = round(rear_base * surface_factor * tube_factor)

    # Safety clamps
    front_psi = max(38, min(110, front_psi))
    rear_psi = max(42, min(115, rear_psi))

    front_bar = round(front_psi * 0.0689476, 1)
    rear_bar = round(rear_psi * 0.0689476, 1)

    # Hookless rim safety threshold is 72.5 PSI (5.0 Bar)
    hookless_warning = bool(front_psi > 72 or rear_psi > 72)

    return {
        "rider_weight": rider_w,
        "bike_weight": bike_w,
        "total_weight": total_sys_kg,
        "tire_width": w_mm,
        "is_tubeless": is_tubeless,
        "is_wet_rough": is_wet_rough,
        "front_psi": front_psi,
        "front_bar": front_bar,
        "rear_psi": rear_psi,
        "rear_bar": rear_bar,
        "hookless_warning": hookless_warning,
    }


def format_tire_pressure_card(result: Dict[str, Any], lang: str = "zh_hant") -> str:
    r_w = result["rider_weight"]
    b_w = result["bike_weight"]
    tot_w = result["total_weight"]
    w = result["tire_width"]
    f_psi = result["front_psi"]
    f_bar = result["front_bar"]
    r_psi = result["rear_psi"]
    r_bar = result["rear_bar"]
    is_tl = result["is_tubeless"]
    hookless = result["hookless_warning"]

    if lang == "en":
        setup_str = "Tubeless" if is_tl else "Standard Tube (Butyl/TPU)"
        lines = [
            f"🎯 <b>Scientific Road Tire Pressure Recommendation</b>",
            f"───────────────",
            f"👤 <b>Rider</b>: {r_w:.0f} kg | <b>Bike & Gear</b>: {b_w:.1f} kg (Total: {tot_w:.1f} kg)",
            f"🚲 <b>Nominal Width</b>: {w:.0f} mm | <b>Setup</b>: {setup_str}",
            f"",
            f"🔵 <b>Front Tire (45% Dynamic Load)</b>: <b>{f_psi} PSI</b> ({f_bar} Bar)",
            f"🔴 <b>Rear Tire (55% Dynamic Load)</b>: <b>{r_psi} PSI</b> ({r_bar} Bar)",
            f"",
            f"💡 <i>Scientific Basis: Calibrated to Silca's impedance breakpoint & SRAM AXS models for 19-21mm internal rim width.</i>",
        ]
        if not is_tl:
            tl_f = round(f_psi * 0.92)
            tl_r = round(r_psi * 0.92)
            lines.append(f"• If switching to <b>Tubeless</b>: ~<b>{tl_f} PSI</b> Front / ~<b>{tl_r} PSI</b> Rear")
        lines.append(f"• Rough/Wet pavement: lower by ~<b>5-10%</b> for extra rubber compliance.")

        if hookless:
            lines.extend([
                f"",
                f"⚠️ <b>Hookless Rim Warning</b>: ISO/ETRTO max limit for hookless rims is strictly <b>72.5 PSI (5.0 Bar)</b>! Do not exceed. If required pressure exceeds 72.5 PSI, upgrade to 28c or 30c tires."
            ])
        return "\n".join(lines)
    else:
        setup_str = "無內胎 / 真空胎 (Tubeless)" if is_tl else "普通內胎 (丁基/TPU)"
        lines = [
            f"🎯 <b>公路車前後輪科學胎壓推薦</b>",
            f"───────────────",
            f"👤 <b>車手體重</b>：{r_w:.0f} kg ｜ <b>車重裝備預設</b>：{b_w:.1f} kg（系統總重：{tot_w:.1f} kg）",
            f"🚲 <b>外胎規格</b>：{w:.0f} mm ｜ <b>氣密系統</b>：{setup_str}",
            f"",
            f"🔵 <b>前輪（45% 動態載荷）</b>：<b>{f_psi} PSI</b>（{f_bar} Bar）",
            f"🔴 <b>後輪（55% 動態載荷）</b>：<b>{r_psi} PSI</b>（{r_bar} Bar）",
            f"",
            f"💡 <i>科學依據：基於 Silca 現代寬胎滾阻阻抗轉折點模型（Impedance Breakpoint）與 19-21mm 內寬輪圈校準，防止因胎壓過高產生微跳躍造成滾阻暴增。</i>",
        ]
        if not is_tl:
            tl_f = round(f_psi * 0.92)
            tl_r = round(r_psi * 0.92)
            lines.append(f"• 若改為<b>真空胎 (Tubeless)</b>：建議降至 前 <b>{tl_f} PSI</b> / 後 <b>{tl_r} PSI</b>")
        lines.append(f"• 粗糙路面/雨天濕滑：建議在推薦值基礎上再下調 <b>5~10%</b> 提升貼地性與抓地力。")

        if hookless:
            lines.extend([
                f"",
                f"⚠️ <b>無鉤輪圈 (Hookless) 安全警示</b>：ISO/ETRTO 規定無鉤碳圈最高氣壓嚴格禁止超過 <b>72.5 PSI (5.0 Bar)</b>！若計算結果超標，強烈建議更換 28c/30c 以上寬胎以降低工作氣壓，切勿超壓！"
            ])
        return "\n".join(lines)

