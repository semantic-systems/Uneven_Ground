from collections import defaultdict
from math import ceil
from typing import List, Dict

import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt


def create_datasets(data_input, ref_pids_to_idx, pid_to_idx, k, normalize_by):
    datasets = []
    for key, value in data_input.items():
        data = np.zeros((len(pid_to_idx), k))
        number_of_statements = np.zeros(len(pid_to_idx))
        for rel_pid, rel_value in value["ref_counter"].items():
            data_point = np.zeros(k)
            sum_counts = 0
            for ref_pid, count in rel_value.items():
                sum_counts += count
                if ref_pid in ref_pids_to_idx:
                    normalized_value = count / value[normalize_by].get(rel_pid, 1)  # Avoid division by zero
                    assert normalized_value <= 1.0
                    data_point[ref_pids_to_idx[ref_pid]] = normalized_value

            if np.any(data_point > 0):
                if rel_pid in pid_to_idx:
                    data[pid_to_idx[rel_pid]] = data_point
            if rel_pid in pid_to_idx:
                number_of_statements[pid_to_idx[rel_pid]] = value[normalize_by].get(rel_pid, 0)
        datasets.append((key, data, number_of_statements))
    return datasets

def plot(data_input, ref_pids_to_idx, pid_to_idx, pid_labels, x_labels, top_k_relation_pids, output_directory,
         k, normalize_by="claim_counter"):
    data = create_datasets(data_input, ref_pids_to_idx, pid_to_idx, k, normalize_by)[0][1]
    # TODO: unnecessary plotting, replace with clustering only
    g = sns.clustermap(data, cmap="Blues", metric="euclidean", method="ward", cbar=False
                       , figsize=(8, 8))

    reordered_x_indices = g.dendrogram_col.reordered_ind
    reordered_y_indices = g.dendrogram_row.reordered_ind
    reordered_x_indices = {idx: i for i, idx in enumerate(reordered_x_indices)}
    reordered_y_indices = {idx: i for i, idx in enumerate(reordered_y_indices)}
    x_labels = [x_labels[i] for i in reordered_x_indices]
    top_k_relation_pids = [top_k_relation_pids[i] for i in reordered_y_indices]
    plt.close()

    ref_pids_to_idx = {x: reordered_x_indices[y] for x, y in ref_pids_to_idx.items()}
    pid_to_idx = {rel_pid: reordered_y_indices[y] for rel_pid, y in pid_to_idx.items()}

    datasets = create_datasets(data_input, ref_pids_to_idx, pid_to_idx, k, normalize_by)
    number_rows = ceil(len(datasets) / 2)
    fig, axes = plt.subplots(number_rows, 2, figsize=(number_rows * 20, 40))
    for i, (key, data, ns) in enumerate(datasets):
        data = np.round(data, 2)
        sns.heatmap(data, cmap="Blues", cbar=False, annot=True,
                    xticklabels=[pid_labels.get(x, x) for x in x_labels], ax=axes[i // 2, i % 2],
                    yticklabels=[pid_labels.get(x, x) for x in top_k_relation_pids])

        axes[i // 2, i % 2].set_xlabel("Reference PIDs")
        axes[i // 2, i % 2].set_ylabel("Relation PIDs")
        axes[i // 2, i % 2].tick_params(axis='x', rotation=90)


        axes[i // 2, i % 2].set_title(f"Heatmap {key}")

    fig.tight_layout()
    fig.savefig(f"{output_directory}/heatmap_{normalize_by}.png")
    plt.close(fig)

    # Collect averages for each dataset
    averages = []
    labels = []
    for key, data, ns in datasets:
        data = np.round(data, 2)
        average = np.mean(data, axis=0)
        averages.append(average)
        labels.append(key)

    # Prepare parameters for grouped bar plot
    num_datasets = len(averages)
    bar_width = 0.8 / num_datasets
    index = np.arange(len(x_labels))
    full_bar_width = bar_width * num_datasets

    # Create figure
    fig = plt.figure(figsize=(number_rows * 20, 40))  # or a fixed size like (20, 10) if desired

    for i, avg in enumerate(averages):
        plt.bar(index + i * bar_width, avg, bar_width, label=labels[i])

    # Set x-ticks with PID labels
    offset = 0.5 * (full_bar_width - bar_width)
    plt.xticks(index + offset, [pid_labels.get(x, x) for x in x_labels], rotation=90)

    # Add labels and title
    plt.xlabel("Relation PIDs")
    plt.ylabel("Average")
    plt.title("Grouped Bar Plot of All Datasets")
    plt.legend()

    fig.tight_layout()
    fig.savefig(f"{output_directory}/macro_bar_{normalize_by}.png")
    plt.close(fig)


    for idx, (key, data, ns) in enumerate(datasets):
        if len(datasets[idx + 1:]) == 0:
            break
        fig, axes = plt.subplots(1, len(datasets) - 1, figsize=((len(datasets) - 1 )* 20, 10))
        for idx2, (key2, data2, ns_2) in enumerate(datasets[idx + 1:]):
            diff = data - data2
            # Round the values to 2 decimal places
            diff = np.round(diff, 2)
            sns.heatmap(diff, annot=True, cmap="coolwarm", cbar=False,
                        xticklabels=[pid_labels.get(x, x) for x in x_labels], ax=axes[idx2], vmax=1.0, vmin=-1.0,
                        yticklabels=[pid_labels.get(x, x) for x in top_k_relation_pids])

            axes[idx2].set_title(f"Heatmap {key} - {key2}")
        fig.tight_layout()
        fig.savefig(f"{output_directory}/heatmap_diff_{key}_{normalize_by}.png")
        plt.close(fig)
def plot_heatmaps(data_input: Dict[str, dict], output_directory, pid_labels: dict = None, k=50, filter_list=None):
    if pid_labels is None:
        pid_labels = {}
    if filter_list is None:
        filter_list = set()
    ref_pid_counter = defaultdict(int)
    rel_pid_counter = defaultdict(int)
    rel_with_ref_pid_counter = defaultdict(int)
    ref_pid_counters  = []
    all_pids = set()
    for category, elem in data_input.items():
        inner_ref_pid_counter = defaultdict(int)
        for pid, claim_references in elem['ref_counter'].items():
            for ref_pid, counter in claim_references.items():
                ref_pid_counter[ref_pid] += counter
                inner_ref_pid_counter[ref_pid] += counter
            all_pids.add(pid)
        for pid, counter in elem["claim_counter"].items():
            rel_pid_counter[pid] += counter
        for pid, counters in elem['num_references'].items():
            counters = {int(k): v for k, v in counters.items()}
            acc = 0
            for key, val in counters.items():
                if key > 0:
                   acc += val
            if pid in ref_pid_counter:
                rel_with_ref_pid_counter[pid] += acc
        overall_num_statements = sum(elem["claim_counter"].values())
        overall_num_statements_with_no_ref = sum(elem["claim_with_ref_counter"].values())
        inner_ref_pid_counter = {x: y / overall_num_statements for x, y in inner_ref_pid_counter.items()}
        ref_pid_counters.append(inner_ref_pid_counter)
        print(f"Statements with a reference for {category}: {overall_num_statements_with_no_ref / overall_num_statements}")
    common_reference_pids = sorted(ref_pid_counter.items(), key=lambda x: x[1], reverse=True)
    x_labels = common_reference_pids[:k]
    x_labels = [x[0] for x in x_labels]
    # ref_pid_counters = [sorted([(a, b) for a,b in x.items() if a in x_labels], key=lambda x: x[1], reverse=True) for x in ref_pid_counters]

    rel_pid_counter = {x: y for x, y in rel_pid_counter.items() if y > 1000}

    common_relation_pids = sorted(rel_pid_counter.items(), key=lambda x: x[1], reverse=True)
    common_relation_pids = [x for x in common_relation_pids if x[0] not in filter_list]
    top_k_relation_pids = common_relation_pids[:k]
    top_k_relation_pids = [x[0] for x in top_k_relation_pids]


    ref_pids_to_idx = {x: idx for idx, x in enumerate(x_labels)}
    pid_to_idx = {rel_pid: idx for idx, rel_pid in enumerate(top_k_relation_pids)}

    plot(data_input, ref_pids_to_idx, pid_to_idx, pid_labels, x_labels, top_k_relation_pids, output_directory, k=k, normalize_by="claim_counter")
    plot(data_input, ref_pids_to_idx, pid_to_idx, pid_labels, x_labels, top_k_relation_pids, output_directory, k=k, normalize_by="claim_with_ref_counter")


def plot_grouped_histograms(data_input: Dict[str, dict], field: str, output_directory: str, pid_labels: dict = None, filter_list= None, k=50):
    if pid_labels is None:
        pid_labels = {}
    if filter_list is None:
        filter_list = set()
    rel_pid_counter = defaultdict(int)
    all_pids = set()
    for elem in data_input.values():
        for pid, claim_references in elem["ref_counter"].items():
            all_pids.add(pid)
        for pid, counter in elem[field].items():
            rel_pid_counter[pid] += counter


    common_relation_pids = sorted(rel_pid_counter.items(), key=lambda x: x[1], reverse=True)
    common_relation_pids = [x for x in common_relation_pids if x[0] not in filter_list]
    top_k_relation_pids = common_relation_pids[:k]
    top_k_relation_pids = [x[0] for x in top_k_relation_pids]

    bars = []
    legend = []
    for income_class, elem in data_input.items():
        bar = [0] * len(top_k_relation_pids)
        for pid, counter in elem[field].items():
            if pid in top_k_relation_pids:
                bar[top_k_relation_pids.index(pid)] = counter / elem["person_counter"]
        bars.append(bar)
        legend.append(income_class)

    full_bar_width = 2
    bar_width = full_bar_width / len(bars)
    group_spacing = 1.5

    index = np.arange(len(top_k_relation_pids)) * group_spacing * full_bar_width

    fig = plt.figure(figsize=(20, 10))
    for i, bar in enumerate(bars):
        plt.bar(index + i * bar_width, bar, bar_width, label=f"Dataset {i + 1}")

    plt.xlabel("Relation PIDs")
    plt.ylabel(f"Normalized {field}")

    plt.title("Grouped Histograms of Relation PIDs")
    offset = 0.5 * (full_bar_width - bar_width)
    plt.xticks(index + offset, [pid_labels.get(x, x) for x in top_k_relation_pids], rotation=75)
    plt.legend(legend)
    fig.tight_layout()
    plt.savefig(f"{output_directory}/{field}.png")
    plt.close(fig)










