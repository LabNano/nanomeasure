from imgui_bundle import imgui, portable_file_dialogs as pfd

def open_file_path(title = "NanoMeasure Open File"):
    p = pfd.open_file(title)
    return p.result()

def save_file_path(title = "NanoMeasure Save File", default_path = None):
    p = pfd.save_file(title, default_path)
    return p.result()

def make_tab_visible(name: str):
    window = imgui.internal.find_window_by_name(name)
    if not window or not window.dock_node or not window.dock_node.tab_bar:
        return
    window.dock_node.tab_bar.next_selected_tab_id = window.tab_id

def generate_dock_binary_tree(initial_id: "imgui.ID", num_leaves):
    if num_leaves <= 1:
        _ = imgui.internal.dock_builder_split_node(initial_id, imgui.Dir.down, 0.5)
        left, right = _.id_at_opposite_dir, _.id_at_dir
        return [left]
    
    nodes = {}
    queue = [(initial_id, False)] # (node_id, is_right_split)
    leaves = []

    while len(leaves) < num_leaves:
        current, is_right_split = queue.pop(0)
        if is_right_split:
            _ = imgui.internal.dock_builder_split_node(current, imgui.Dir.right, 0.5)
            left, right = _.id_at_opposite_dir, _.id_at_dir
        else:
            _ = imgui.internal.dock_builder_split_node(current, imgui.Dir.down, 0.5)
            left, right = _.id_at_opposite_dir, _.id_at_dir
    
        nodes[current] = (left, right)

        queue.append((left, not is_right_split))
        queue.append((right, not is_right_split))

        if len(queue) + len(leaves) >= num_leaves:
            # Mark the remaining queue as leaves and stop splitting
            leaves.extend(node_id for node_id, _ in queue)
            queue.clear()
    return leaves
