def get_next_update_partition(partition_module=None):
    if partition_module is None:
        from esp32 import Partition
        partition_module = Partition

    current = partition_module(partition_module.RUNNING)
    current_label = current.info()[4]
    next_label = "ota_0" if current_label == "ota_1" else "ota_1"
    partitions = partition_module.find(
        partition_module.TYPE_APP,
        label=next_label
    )
    if not partitions:
        raise Exception(f"Could not find partition: {next_label}")
    return partitions[0]
