import os
import yaml

G_DEFAULT = 9.80665

def read_spec(path="spec/celentrail.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    spec = read_spec()
    os.makedirs("reports", exist_ok=True)

    m = float(spec["loads"]["total_mass_kg"])
    g = float(spec["loads"].get("gravity_m_s2", G_DEFAULT))
    W = m * g  # N

    x_mm = float(spec["loads"]["center_of_mass_offset_x"])
    base_mm = float(spec["loads"]["roller_base_width"])

    x = x_mm / 1000.0      # m
    base = base_mm / 1000.0 # m

    M = W * x  # N*m
    F = M / base if base > 0 else 0.0

    lines = []
    lines.append("# Celentrail — latest report\n\n")
    lines.append("## Входные данные (из spec/celentrail.yaml)\n")
    lines.append(f"- Масса: **{m:.2f} kg**\n")
    lines.append(f"- g: **{g:.5f} m/s²**\n")
    lines.append(f"- Плечо x: **{x_mm:.1f} mm**\n")
    lines.append(f"- База роликов (L-R): **{base_mm:.1f} mm**\n\n")

    lines.append("## Быстрые оценки\n")
    lines.append(f"- Вес W = m·g: **{W:.1f} N**\n")
    lines.append(f"- Момент M = W·x: **{M:.1f} N·m**\n")
    lines.append(f"- Эквивалентная пара сил F ≈ M/base: **{F:.1f} N**\n\n")

    lines.append("## Примечание\n")
    lines.append("Это быстрый контроль по формулам. Полный сопромат делается в SimScale по **cad/latest.step**.\n")

    with open("reports/latest.md", "w", encoding="utf-8") as f:
        f.write("".join(lines))

if __name__ == "__main__":
    main()
