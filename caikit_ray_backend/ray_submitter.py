# Copyright The Caikit Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Standard
import base64
import os
import json
import pickle

# Third Party
import ray

# First Party
import alog

# Local
from caikit_ray_backend.ray_training_actor import RayTrainingActor
from caikit.core.toolkit.errors import error_handler

log = alog.use_channel("RAYTRN")
error = error_handler.get(log)

def txt_to_obj(txt):
    base64_bytes = txt.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    obj = pickle.loads(message_bytes)
    return obj

def main():
    log.debug("Ray job has commenced to kick off training")

    runtime_env = json.loads(os.environ.get("RAY_JOB_CONFIG_JSON_ENV_VAR")).get("runtime_env")

    # Identify our target training module and do basic parameter validation.
    # We don't validate that we can actually import it, the Ray Actor will attempt it later
    module_class_ref = runtime_env.get("module_class")
    error.value_check("<RYT46582584E>", module_class_ref is not None)
    module_class = txt_to_obj(module_class_ref)
    error.type_check("<RYT97664954E>", str, module_class=module_class)

    # Even if either value is None, it's fine.
    num_gpus = os.environ.get("num_gpus")
    num_cpus = os.environ.get("num_cpus")

    # Instantiate the remote Ray Actor with our target module class for training
    remote_class = ray.remote(num_cpus=num_cpus, num_gpus=num_gpus)(
         RayTrainingActor).remote(module_class=module_class)

    # The entire kwargs dict should have been serialized as a whole
    serialized_kwargs = runtime_env.get("kwargs").get("kwargs")
    if serialized_kwargs:
        kwargs = txt_to_obj(serialized_kwargs)
        error.type_check("<RYT26466208E>", dict, kwargs=kwargs)
    else:
        kwargs = {}

    # Deserialize each item in the args list
    serialized_args = runtime_env.get("args")
    args = []
    for arg in serialized_args:
        args.append(txt_to_obj(arg))

    model_path = runtime_env.get("model_path")
    if model_path:
        model_path = txt_to_obj(model_path)
        error.type_check("<RYT70238308E>", str, model_path=model_path)

    # Finally kick off trainig
    with alog.ContextTimer(
        log.debug, "Done training %s in: ", module_class
    ):
        remote_class.train_and_save.remote(model_path, *args, **kwargs)


if __name__ == "__main__":
    main()