#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revestimento de Reservatórios Cilíndricos
Integral de superfície + banco de materiais + visualização da aplicação
=======================================================================

    Q = ∬_S c(x, y, z) dS      (c constante  ->  Q = c · A)

Uso:
    python reservatorio_revestimento.py --listar
    python reservatorio_revestimento.py --material 1 --raio 2 --altura 3
    python reservatorio_revestimento.py --interativo
    python reservatorio_revestimento.py --material 4 --sem-janelas

Bibliotecas: NumPy, Matplotlib (obrigatórias) e SymPy (opcional, para
mostrar as integrais simbólicas).

AVISO: os valores do banco de materiais são faixas TÍPICAS para estudo.
Confirme sempre na ficha técnica do fabricante (principalmente a
adequação para água potável).
"""

import argparse
import math
import os
from dataclasses import dataclass, replace

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from matplotlib.widgets import Slider

try:
    import sympy as sp
except ImportError:  # SymPy é opcional
    sp = None

PASTA_SAIDA = "figuras"
DPI = 300
COR_CONCRETO = "#b9bbb4"
COR_AGUA = "#9fd0dc"


# =============================================================================
# 1. BANCO DE MATERIAIS
# =============================================================================
@dataclass(frozen=True)
class Material:
    nome: str
    tipo: str
    cor: str                 # cor usada nos gráficos
    consumo_min: float       # kg/m² (todas as demãos)
    consumo_max: float
    consumo_tipico: float
    espessura_mm: float      # espessura seca total
    densidade: float         # g/cm³
    demaos: int
    intervalo: str           # intervalo entre demãos
    cura: str
    potavel: str
    submersao: str
    flexibilidade: str
    pressao_negativa: str
    vida_util: str
    embalagem_kg: float
    obs: str


MATERIAIS = [
    Material("Argamassa polimérica flexível", "Cimentício bicomponente", "#7f8f93",
             3.0, 4.0, 3.5, 2.0, 1.8, 3, "4–6 h", "7 dias",
             "Sim (linhas certificadas)", "Sim", "Média", "Limitada", "10–15 anos", 18,
             "Muito usada em caixas e cisternas de concreto; aceita pequenas fissuras."),
    Material("Cimentício de cristalização", "Cristalizante", "#b4ae9f",
             0.8, 1.5, 1.5, 1.0, 1.5, 2, "2–4 h", "3 dias úmida",
             "Sim", "Sim", "Rígido", "Sim", "15–25 anos", 18,
             "Penetra nos poros do concreto e sela por cristais; exige substrato úmido."),
    Material("Argamassa impermeável rígida", "Cimentício aditivado", "#9da39a",
             4.0, 6.0, 5.0, 2.6, 1.9, 3, "6 h", "7 dias",
             "Sim", "Sim", "Rígido", "Sim", "10–20 anos", 25,
             "Barata e durável, mas não acompanha fissuras."),
    Material("Epóxi bicomponente p/ água potável", "Epóxi poliamina", "#6aa6c6",
             0.4, 0.8, 0.6, 0.3, 1.4, 2, "12–24 h", "7 dias",
             "Sim (versões certificadas)", "Sim", "Rígido", "Parcial", "8–12 anos", 3.6,
             "Filme fino e liso, fácil de higienizar. Exige substrato seco e preparo."),
    Material("Epóxi novolac", "Epóxi química", "#4f7160",
             0.8, 1.2, 1.0, 0.5, 1.5, 2, "12–24 h", "7 dias",
             "Não", "Sim", "Rígido", "Parcial", "12–20 anos", 3.6,
             "Indicado para esgoto e produtos químicos, não para água potável."),
    Material("Poliuréia pura (spray)", "Elastômero", "#5b6168",
             2.0, 3.0, 2.2, 2.0, 1.05, 1, "Minutos", "24 h",
             "Depende da certificação", "Sim", "Alta", "Sim (com primer)", "20+ anos", 200,
             "Cura rápida e alta elasticidade. Exige equipamento e aplicador treinado."),
    Material("Poliuretano moldado in loco", "Membrana PU", "#8d7b6b",
             1.5, 2.5, 2.0, 1.5, 1.1, 3, "8–12 h", "5 dias",
             "Algumas linhas", "Linhas específicas", "Alta", "Limitada", "10–15 anos", 18,
             "Boa para lajes e tampas; para submersão use só o produto indicado."),
    Material("Manta asfáltica 4 mm", "Betuminoso", "#2f3133",
             4.5, 5.2, 4.8, 4.0, 1.2, 1, "–", "Imediata",
             "Não", "Não", "Alta", "Não", "10–15 anos", 48,
             "Para cobertura e áreas externas; não usar com água potável."),
    Material("Membrana acrílica", "Acrílico", "#e4e6df",
             1.0, 1.5, 1.2, 0.5, 1.3, 4, "4–6 h", "3 dias",
             "Não", "Não", "Média", "Não", "5–8 anos", 18,
             "Proteção de lajes de cobertura e tampas. Não resiste a submersão."),
    Material("PRFV (laminado de fibra de vidro)", "Resina + fibra", "#6c9f72",
             3.0, 5.0, 4.0, 2.7, 1.5, 3, "1–3 h", "3 dias",
             "Sim (resina grau alimentício)", "Sim", "Rígido", "Sim", "20+ anos", 25,
             "Forma uma casca resistente; custo alto e mão de obra especializada."),
]


def listar_materiais() -> None:
    print(f"\n{'Nº':>3}  {'Material':<38}{'c (kg/m²)':>12}{'Esp.(mm)':>9}{'Demãos':>7}  Água potável")
    print("-" * 100)
    for i, m in enumerate(MATERIAIS, 1):
        print(f"{i:>3}  {m.nome:<38}{m.consumo_min:>5.1f}–{m.consumo_max:<5.1f}"
              f"{m.espessura_mm:>8.1f}{m.demaos:>7}  {m.potavel}")


def ficha(m: Material) -> None:
    sep = "=" * 66
    print(f"\n{sep}\nFICHA: {m.nome}\n{sep}")
    for rot, val in (("Tipo", m.tipo),
                     ("Faixa de consumo", f"{m.consumo_min:g} a {m.consumo_max:g} kg/m²"),
                     ("Intervalo entre demãos", m.intervalo), ("Cura total", m.cura),
                     ("Água potável", m.potavel), ("Submersão contínua", m.submersao),
                     ("Flexibilidade", m.flexibilidade),
                     ("Pressão negativa", m.pressao_negativa),
                     ("Vida útil típica", m.vida_util), ("Observações", m.obs)):
        print(f"  {rot:<24}{val}")


# =============================================================================
# 2. PARÂMETROS E VALIDAÇÃO
# =============================================================================
@dataclass
class Parametros:
    raio_m: float = 2.0
    altura_m: float = 3.0
    revestir_lateral: bool = True
    revestir_fundo: bool = True
    perdas_percent: float = 10.0
    material: Material = MATERIAIS[0]
    consumo_kg_m2: float = 3.5      # c [kg/m²]  (consumo total, todas as demãos)
    demaos: int = 3
    espessura_mm: float = 2.0
    densidade: float = 1.8
    embalagem_kg: float = 18.0

    @classmethod
    def de_material(cls, m: Material, **kw) -> "Parametros":
        base = dict(material=m, consumo_kg_m2=m.consumo_tipico, demaos=m.demaos,
                    espessura_mm=m.espessura_mm, densidade=m.densidade,
                    embalagem_kg=m.embalagem_kg)
        base.update({k: v for k, v in kw.items() if v is not None})
        return cls(**base)


def validar(p: Parametros) -> None:
    nums = [p.raio_m, p.altura_m, p.perdas_percent, p.consumo_kg_m2,
            p.espessura_mm, p.densidade, p.embalagem_kg]
    if not all(math.isfinite(v) for v in nums):
        raise ValueError("Todos os parâmetros devem ser números finitos.")
    if p.raio_m <= 0 or p.altura_m <= 0:
        raise ValueError("Raio e altura devem ser positivos.")
    if p.embalagem_kg <= 0 or p.densidade <= 0 or p.espessura_mm <= 0:
        raise ValueError("Embalagem, densidade e espessura devem ser positivas.")
    if p.consumo_kg_m2 < 0 or p.perdas_percent < 0:
        raise ValueError("Consumo e perdas não podem ser negativos.")
    if p.demaos < 1:
        raise ValueError("O número de demãos deve ser pelo menos 1.")
    if not (p.revestir_lateral or p.revestir_fundo):
        raise ValueError("Revesta pelo menos a parede lateral ou o fundo.")


# =============================================================================
# 3. INTEGRAIS DE SUPERFÍCIE
# =============================================================================
def integrais_simbolicas() -> None:
    """Mostra dS = ‖r_u × r_v‖ du dv e as áreas (requer SymPy)."""
    if sp is None:
        print("\n(SymPy não instalado: pulando integrais simbólicas. pip install sympy)")
        return
    R, H = sp.symbols("R H", positive=True)
    th, z = sp.symbols("theta z", real=True)
    rho = sp.Symbol("rho", nonnegative=True)

    r_lat = sp.Matrix([R * sp.cos(th), R * sp.sin(th), z])
    n_lat = sp.simplify(sp.sqrt(sum(c ** 2 for c in
                        r_lat.diff(th).cross(r_lat.diff(z)).applyfunc(sp.simplify))))
    A_lat = sp.integrate(sp.integrate(n_lat, (z, 0, H)), (th, 0, 2 * sp.pi))

    r_fun = sp.Matrix([rho * sp.cos(th), rho * sp.sin(th), 0])
    n_fun = sp.simplify(sp.sqrt(sum(c ** 2 for c in
                        r_fun.diff(rho).cross(r_fun.diff(th)).applyfunc(sp.simplify))))
    A_fun = sp.integrate(sp.integrate(n_fun, (rho, 0, R)), (th, 0, 2 * sp.pi))

    print("\nINTEGRAIS SIMBÓLICAS (SymPy)")
    print(f"  Parede lateral: dS = {n_lat} dθ dz   ->  A_lat = {sp.simplify(A_lat)}")
    print(f"  Fundo:          dS = {n_fun} dρ dθ   ->  A_fun = {sp.simplify(A_fun)}")


def integracao_numerica(p: Parametros, n_th=200, n_z=20, n_rho=20) -> dict:
    """Ponto médio em θ (periódico) e Gauss-Legendre em z e ρ."""
    h = 2 * np.pi / n_th
    th = (np.arange(n_th) + 0.5) * h

    def gl(n, a, b):
        x, w = np.polynomial.legendre.leggauss(n)
        return 0.5 * (b - a) * x + 0.5 * (b + a), 0.5 * (b - a) * w

    zz, wz = gl(n_z, 0, p.altura_m)
    rr, wr = gl(n_rho, 0, p.raio_m)
    # dS_lat = R ; dS_fundo = ρ
    A_lat = float(np.sum(np.outer(np.full(n_th, h), wz) * p.raio_m))
    A_fun = float(np.sum(np.outer(wr * rr, np.full(n_th, h))))
    return {"A_lat": A_lat, "A_fun": A_fun}


# =============================================================================
# 4. ESTIMATIVA DO CONSUMO
# =============================================================================
def estimar(p: Parametros) -> dict:
    A_lat = 2 * math.pi * p.raio_m * p.altura_m if p.revestir_lateral else 0.0
    A_fun = math.pi * p.raio_m ** 2 if p.revestir_fundo else 0.0
    A = A_lat + A_fun
    Q = p.consumo_kg_m2 * A
    Qp = Q * (1 + p.perdas_percent / 100)
    n = math.ceil(Qp / p.embalagem_kg - 1e-12)
    comprada = n * p.embalagem_kg
    return {"A_lat": A_lat, "A_fun": A_fun, "A_tot": A, "Q_teorico": Q,
            "Q_estimado": Qp, "n_emb": n, "massa_comprada": comprada,
            "sobra": comprada - Qp, "volume_L": Qp / p.densidade}


def consumo_para_raio(R: float, p: Parametros) -> float:
    A = (2 * math.pi * R * p.altura_m if p.revestir_lateral else 0) + \
        (math.pi * R ** 2 if p.revestir_fundo else 0)
    return p.consumo_kg_m2 * A * (1 + p.perdas_percent / 100)


def exibir(p: Parametros, res: dict) -> None:
    sep = "=" * 66
    print(f"\n{sep}\nPARÂMETROS\n{sep}")
    print(f"  Material                = {p.material.nome}")
    print(f"  Raio / Altura           = {p.raio_m:g} m / {p.altura_m:g} m")
    print(f"  Lateral / Fundo         = {'sim' if p.revestir_lateral else 'não'} / "
          f"{'sim' if p.revestir_fundo else 'não'}")
    print(f"  Consumo c               = {p.consumo_kg_m2:g} kg/m² em {p.demaos} demão(ões)")
    print(f"  Perdas                  = {p.perdas_percent:g} %")
    print(f"  Embalagem               = {p.embalagem_kg:g} kg")
    print(f"\n{sep}\nRESULTADOS\n{sep}")
    print(f"  Área lateral (2πRH)     = {res['A_lat']:.4f} m²")
    print(f"  Área do fundo (πR²)     = {res['A_fun']:.4f} m²")
    print(f"  Área total              = {res['A_tot']:.4f} m²")
    print(f"  Consumo teórico         = {res['Q_teorico']:.4f} kg")
    print(f"  Consumo com perdas      = {res['Q_estimado']:.4f} kg  (~{res['volume_L']:.1f} L)")
    print(f"  Embalagens (↑)          = {res['n_emb']} un. de {p.embalagem_kg:g} kg")
    print(f"  Massa adquirida         = {res['massa_comprada']:.4f} kg")
    print(f"  Sobra estimada          = {res['sobra']:.4f} kg")
    num = integracao_numerica(p)
    A_num = (num["A_lat"] if p.revestir_lateral else 0) + (num["A_fun"] if p.revestir_fundo else 0)
    print(f"  Verificação numérica    = {A_num:.10f} m²  (erro {abs(A_num - res['A_tot']):.2e})")
    print("\n  AVISO: rugosidade, porosidade, método de aplicação e espessura efetiva\n"
          "  alteram o consumo real. Confirme na ficha técnica do fabricante.")


# =============================================================================
# 5. GRÁFICOS
# =============================================================================
def _proporcional(ax, R, H):
    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)
    ax.set_zlim(0, max(H, 2 * R))
    ax.set_box_aspect((2 * R, 2 * R, max(H, 2 * R)))


def desenhar_modelo(ax, p: Parametros, demaos_aplicadas: int = None) -> None:
    """Modelo 3D com corte visual. A opacidade do revestimento cresce a cada demão."""
    R, H = p.raio_m, p.altura_m
    k = p.demaos if demaos_aplicadas is None else demaos_aplicadas
    alfa = k / p.demaos
    cor = p.material.cor
    corte = np.deg2rad(50)
    th = np.linspace(corte, 2 * np.pi - corte, 120)
    TH, ZZ = np.meshgrid(th, np.linspace(0, H, 2))
    X, Y = R * np.cos(TH), R * np.sin(TH)
    ax.plot_surface(X, Y, ZZ, color=COR_CONCRETO, alpha=0.45, linewidth=0, shade=True)
    if p.revestir_lateral and alfa > 0:
        ax.plot_surface(X, Y, ZZ, color=cor, alpha=0.2 + 0.6 * alfa, linewidth=0, shade=True)

    RHO, THF = np.meshgrid(np.linspace(0, R, 30), np.linspace(0, 2 * np.pi, 120))
    XF, YF = RHO * np.cos(THF), RHO * np.sin(THF)
    ax.plot_surface(XF, YF, np.zeros_like(RHO), color=COR_CONCRETO, alpha=0.9, linewidth=0)
    if p.revestir_fundo and alfa > 0:
        ax.plot_surface(XF, YF, np.zeros_like(RHO) + 0.01, color=cor,
                        alpha=0.15 + 0.8 * alfa, linewidth=0)

    ax.plot(R * np.cos(th), R * np.sin(th), H, color="k", lw=1.2)
    for s in (corte, -corte):
        ax.plot([R * np.cos(s)] * 2, [R * np.sin(s)] * 2, [0, H], color="k", lw=1.2)
    ax.plot([0, -R], [0, 0], [0, 0], "k--", lw=2)
    ax.text(-R / 2, 0, 0.05 * H, f"R = {R:g} m", ha="center", fontweight="bold")
    xs, ys = R * np.cos(-corte), R * np.sin(-corte)
    ax.plot([xs, xs], [ys, ys], [0, H], color="crimson", lw=3)
    ax.text(xs * 1.12, ys * 1.12, H / 2, f"H = {H:g} m", color="crimson", fontweight="bold")
    _proporcional(ax, R, H)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")
    ax.view_init(elev=24, azim=25)
    ax.legend(handles=[Patch(color=cor, label=p.material.nome),
                       Patch(color=COR_CONCRETO, label="Concreto")],
              loc="upper left", fontsize=8)


def desenhar_corte(ax, p: Parametros, demaos_aplicadas: int = None) -> None:
    """Corte esquemático: concreto | demãos | água (espessura exagerada)."""
    k = p.demaos if demaos_aplicadas is None else demaos_aplicadas
    esp_px = min(1.7, max(0.24, p.espessura_mm * 0.4))
    w = esp_px / p.demaos
    x0 = 1.4
    ax.add_patch(Rectangle((0.2, 0), 1.2, 1.6, color=COR_CONCRETO))
    ax.add_patch(Rectangle((x0 + esp_px, 0), 4.0 - x0 - esp_px, 1.6, color=COR_AGUA))
    for i in range(p.demaos):
        on = i < k
        ax.add_patch(Rectangle((x0 + i * w, 0), w, 1.6,
                               facecolor=p.material.cor if on else "none",
                               alpha=(0.8 if i % 2 == 0 else 1.0) if on else 1,
                               edgecolor="k" if on else "gray",
                               ls="-" if on else "--", lw=1))
    ax.text(0.8, -0.15, "Concreto", ha="center", va="top")
    ax.text(x0 + esp_px + (4.0 - x0 - esp_px) / 2, -0.15, "Água", ha="center", va="top")
    ax.text(x0 + esp_px / 2, 1.7,
            f"{k}/{p.demaos} demãos · {p.espessura_mm * k / p.demaos:.2f} mm",
            ha="center", va="bottom", fontsize=9)
    ax.set_xlim(0, 4.0)
    ax.set_ylim(-0.4, 2.0)
    ax.axis("off")
    ax.set_title("Corte da parede (espessura exagerada)")


def figura_painel(p: Parametros, res: dict) -> plt.Figure:
    fig = plt.figure(figsize=(14, 8))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.15, 1], height_ratios=[1, 0.9])
    ax3d = fig.add_subplot(gs[:, 0], projection="3d")
    desenhar_modelo(ax3d, p)
    ax3d.set_title("Reservatório revestido (vista com corte)")
    axc = fig.add_subplot(gs[0, 1])
    desenhar_corte(axc, p)
    axt = fig.add_subplot(gs[1, 1])
    axt.axis("off")
    txt = (f"{p.material.nome}\n\n"
           f"Área total:            {res['A_tot']:.2f} m²\n"
           f"Consumo teórico:       {res['Q_teorico']:.2f} kg\n"
           f"Com perdas ({p.perdas_percent:g} %):    {res['Q_estimado']:.2f} kg\n"
           f"Embalagens de {p.embalagem_kg:g} kg: {res['n_emb']} un.\n"
           f"Sobra estimada:        {res['sobra']:.2f} kg")
    axt.text(0.02, 0.95, txt, va="top", family="monospace", fontsize=11,
             bbox=dict(boxstyle="round,pad=0.6", fc="#f5f5f5", ec="#888"))
    fig.suptitle("Estimativa de revestimento em reservatório cilíndrico",
                 fontsize=14, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def figura_consumo_raio(p: Parametros, res: dict) -> plt.Figure:
    raios = np.linspace(0.5, max(2 * p.raio_m, 4.0), 200)
    Q = [consumo_para_raio(r, p) for r in raios]
    N = [math.ceil(q / p.embalagem_kg - 1e-12) for q in Q]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(raios, Q, color="#1f77b4", lw=2.5, label="Consumo com perdas (kg)")
    ax.plot(p.raio_m, res["Q_estimado"], "o", color="crimson", ms=10,
            label=f"R = {p.raio_m:g} m → {res['Q_estimado']:.1f} kg")
    ax.set_xlabel("Raio R (m)")
    ax.set_ylabel("Consumo com perdas (kg)")
    ax.grid(alpha=0.3)
    ax2 = ax.twinx()
    ax2.step(raios, N, where="post", color="#2ca02c", ls="--", label="Embalagens (un.)")
    ax2.set_ylabel("Embalagens (un.)")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left")
    ax.set_title(f"{p.material.nome}: consumo × raio (H = {p.altura_m:g} m)")
    fig.tight_layout()
    return fig


def figura_interativa(p: Parametros) -> plt.Figure:
    """Controle deslizante para ver as demãos sendo aplicadas."""
    fig = plt.figure(figsize=(12, 6.5))
    ax3d = fig.add_axes([0.02, 0.15, 0.55, 0.8], projection="3d")
    axc = fig.add_axes([0.6, 0.3, 0.37, 0.55])
    ax_s = fig.add_axes([0.25, 0.04, 0.5, 0.03])
    sl = Slider(ax_s, "Demãos aplicadas", 0, p.demaos, valinit=p.demaos, valstep=1)

    def atualizar(_=None):
        k = int(sl.val)
        ax3d.clear()
        axc.clear()
        desenhar_modelo(ax3d, p, k)
        desenhar_corte(axc, p, k)
        fig.canvas.draw_idle()

    sl.on_changed(atualizar)
    atualizar()
    fig._slider = sl   # evita coleta de lixo
    fig.suptitle(f"Aplicação: {p.material.nome}", fontweight="bold")
    return fig


def salvar_figuras(p: Parametros, res: dict, pasta=PASTA_SAIDA) -> list:
    os.makedirs(pasta, exist_ok=True)
    figs = {"01_painel.png": figura_painel(p, res),
            "02_consumo_vs_raio.png": figura_consumo_raio(p, res)}
    caminhos = []
    for nome, fig in figs.items():
        c = os.path.join(pasta, nome)
        fig.savefig(c, dpi=DPI, bbox_inches="tight")
        caminhos.append(c)
    return caminhos


# =============================================================================
# 6. ENTRADA INTERATIVA NO TERMINAL
# =============================================================================
def _ler(msg, padrao, tipo=float):
    s = input(f"  {msg} [{padrao}]: ").strip().replace(",", ".")
    return tipo(s) if s else padrao


def menu_interativo() -> Parametros:
    listar_materiais()
    i = _ler("Escolha o número do material", 1, int)
    m = MATERIAIS[i - 1]
    ficha(m)
    print("\nDimensões e parâmetros (Enter mantém o valor padrão):")
    return Parametros.de_material(
        m,
        raio_m=_ler("Raio R (m)", 2.0),
        altura_m=_ler("Altura H (m)", 3.0),
        consumo_kg_m2=_ler("Consumo c (kg/m²)", m.consumo_tipico),
        demaos=_ler("Número de demãos", m.demaos, int),
        perdas_percent=_ler("Perdas (%)", 10.0),
        embalagem_kg=_ler("Massa por embalagem (kg)", m.embalagem_kg),
        revestir_lateral=_ler("Revestir parede lateral? (1=sim, 0=não)", 1, int) == 1,
        revestir_fundo=_ler("Revestir fundo? (1=sim, 0=não)", 1, int) == 1,
    )


# =============================================================================
# PROGRAMA PRINCIPAL
# =============================================================================
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--listar", action="store_true", help="lista o banco de materiais")
    ap.add_argument("--interativo", action="store_true", help="pergunta os dados no terminal")
    ap.add_argument("--material", type=int, default=1, help="nº do material (ver --listar)")
    ap.add_argument("--raio", type=float, default=2.0)
    ap.add_argument("--altura", type=float, default=3.0)
    ap.add_argument("--consumo", type=float, help="kg/m² (padrão: valor típico do material)")
    ap.add_argument("--demaos", type=int)
    ap.add_argument("--perdas", type=float, default=10.0)
    ap.add_argument("--embalagem", type=float, help="kg por embalagem")
    ap.add_argument("--sem-fundo", action="store_true")
    ap.add_argument("--sem-lateral", action="store_true")
    ap.add_argument("--sem-janelas", action="store_true", help="só salva os PNGs")
    a = ap.parse_args()

    if a.sem_janelas:
        matplotlib.use("Agg")
    if a.listar:
        listar_materiais()
        return

    if a.interativo:
        p = menu_interativo()
    else:
        if not 1 <= a.material <= len(MATERIAIS):
            ap.error(f"--material deve estar entre 1 e {len(MATERIAIS)}")
        p = Parametros.de_material(
            MATERIAIS[a.material - 1], raio_m=a.raio, altura_m=a.altura,
            consumo_kg_m2=a.consumo, demaos=a.demaos, perdas_percent=a.perdas,
            embalagem_kg=a.embalagem, revestir_lateral=not a.sem_lateral,
            revestir_fundo=not a.sem_fundo)
    validar(p)

    ficha(p.material)
    integrais_simbolicas()
    res = estimar(p)
    exibir(p, res)

    print("\nFiguras salvas:")
    for c in salvar_figuras(p, res):
        print(f"  - {c}")

    if not a.sem_janelas:
        figura_interativa(p)
        plt.show()


if __name__ == "__main__":
    main()