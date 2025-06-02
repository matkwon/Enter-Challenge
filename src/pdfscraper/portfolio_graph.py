import matplotlib.pyplot as plt
import pandas as pd
import json


def df_formatter(df):
    df = df.iloc[:,[-1,0,1]]
    df.columns = ["class", "asset", "position"]
    return df


def graph_generator(portfolio):

    all_port = pd.concat([df_formatter(pd.DataFrame(json.loads(portfolio["message"][c]))) for c in ["stocks", "funds", "fixed_income"]]).sort_values("position")
    all_port["class"] = all_port["class"].map({"funds": "Fundos", "stocks": "Ações", "fixed_income": "Renda Fixa"})

    # 1. Prepare data
    class_summary = all_port.groupby('class')['position'].sum()
    class_labels_orig = class_summary.index.tolist()
    class_sizes = class_summary.values

    asset_labels_orig = []
    asset_sizes = []
    asset_class_map = []
    for class_name in class_labels_orig:
        class_assets = all_port[all_port['class'] == class_name]
        asset_labels_orig.extend(class_assets['asset'].tolist())
        asset_sizes.extend(class_assets['position'].tolist())
        asset_class_map.extend([class_name] * len(class_assets))

    # 2. Define colors
    base_colors = plt.get_cmap('Pastel2')
    class_color_dict = {cls: base_colors(i) for i, cls in enumerate(class_labels_orig)}
    inner_colors = [class_color_dict[cls] for cls in class_labels_orig]
    outer_colors = [class_color_dict[cls] for cls in asset_class_map]

    # 3. Create the graph
    fig, ax = plt.subplots(figsize=(7, 7))

    MAX_ASSET_NAME_LENGTH = 22
    asset_display_labels = [
        (name[:MAX_ASSET_NAME_LENGTH] + '...' if len(name) > MAX_ASSET_NAME_LENGTH else name)
        for name in asset_labels_orig
    ]

    # --- EXTERNaAL RING (ASSETS) ---
    wedges_outer, texts_asset_labels, autotexts_outer_pct = ax.pie(
        asset_sizes,
        labels=asset_display_labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=outer_colors,
        radius=1.0,
        pctdistance=0.91,
        labeldistance=1.08,
        wedgeprops=dict(width=0.4, edgecolor='w')
    )

    # FONT SIZES
    asset_label_fontsize = 7
    asset_pct_fontsize = 6

    for label in texts_asset_labels:
        label.set_fontsize(asset_label_fontsize)

    for autotext in autotexts_outer_pct:
        autotext.set_fontsize(asset_pct_fontsize)
        autotext.set_color('black')

    # --- INTERNAL RING (CLASSES) ---
    class_display_labels = [f"{name}\n({(size/sum(class_sizes)*100):.1f}%)" for name, size in zip(class_labels_orig, class_sizes)]

    wedges_inner, texts_class_labels = ax.pie(
        class_sizes,
        labels=class_display_labels,
        startangle=90,
        colors=inner_colors,
        radius=0.6,
        labeldistance=0.45, # Pequeno ajuste se necessário
        wedgeprops=dict(edgecolor='w')
    )

    # CLASSES FONT SIZE
    class_label_fontsize = 9

    for label in texts_class_labels:
        label.set_fontsize(class_label_fontsize)
        label.set_fontweight('bold')
        label.set_ha('center')

    # TITLE
    title_fontsize = 15
    ax.set_title("Distribuição da Carteira", fontsize=title_fontsize, pad=20) # pad ajustado

    plt.tight_layout()

    # Export
    try:
        plt.savefig("../img/portfolio_graph.png", dpi=300, bbox_inches='tight')
        print("Graph saved as portfolio_graph.png")
    except Exception as e:
        print(f"Error to save graph: {e}")