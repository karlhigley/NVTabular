import os
from shutil import copyfile

import cudf
from google.protobuf import text_format

# read in the triton ModelConfig proto object - generating it if it doesn't exist
try:
    import nvtabular.inference.triton.model_config_pb2 as model_config
except ImportError:
    pwd = os.path.dirname(__file__)
    os.system(f"protoc --python_out={pwd} model_config.proto ")
    import nvtabular.inference.triton.model_config_pb2 as model_config


def generate_triton_model(workflow, name, output_path, version=1):
    """ converts a workflow to a triton mode """
    workflow.save(os.path.join(output_path, str(version), "workflow"))
    _generate_model_config(workflow, name, output_path)
    copyfile(
        os.path.join(os.path.dirname(__file__), "model.py"),
        os.path.join(output_path, str(version), "model.py"),
    )


def _generate_model_config(workflow, name, output_path):
    """given a workflow generates the trton modelconfig proto object describing the inputs
    and outputs to that workflow"""
    config = model_config.ModelConfig(name=name, backend="python")

    input_dtypes = dict(zip(workflow.input_dtypes.index, workflow.input_dtypes))

    for column in workflow.column_group.input_column_names:
        dtype = input_dtypes[column]
        config.input.append(
            model_config.ModelInput(name=column, data_type=_convert_dtype(dtype), dims=[-1])
        )

    for column, dtype in zip(workflow.output_dtypes.index, workflow.output_dtypes):
        config.output.append(
            model_config.ModelOutput(name=column, data_type=_convert_dtype(dtype), dims=[-1])
        )

    with open(os.path.join(output_path, "config.pbtxt"), "w") as o:
        text_format.PrintMessage(config, o)


def _convert_dtype(dtype):
    """ converts a dtype to the appropiate triton proto type """
    if dtype == "float64":
        return model_config.TYPE_FP64
    if dtype == "float32":
        return model_config.TYPE_FP32
    if dtype == "float16":
        return model_config.TYPE_FP16
    if dtype == "int64":
        return model_config.TYPE_INT64
    if dtype == "int32":
        return model_config.TYPE_INT32
    if dtype == "int16":
        return model_config.TYPE_INT16
    if dtype == "int8":
        return model_config.TYPE_INT8
    if dtype == "uint64":
        return model_config.TYPE_UINT64
    if dtype == "uint32":
        return model_config.TYPE_UINT32
    if dtype == "uint16":
        return model_config.TYPE_UINT16
    if dtype == "uint8":
        return model_config.TYPE_UINT8
    if dtype == "bool":
        return model_config.TYPE_BOOL
    if cudf.utils.dtypes.is_string_dtype(dtype):
        return model_config.TYPE_STRING
    raise ValueError(f"Can't convert dtype {dtype})")