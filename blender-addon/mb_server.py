# Copyright 2015 gRPC authors.
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
"""The Python implementation of the GRPC helloworld.ViewService server."""

from concurrent import futures

import grpc
import bpy
import queue
from . import mb_scene
from . import mastodon_blender_view_pb2 as pb
from . import mastodon_blender_view_pb2_grpc as rpc
from . import mb_utils
from functools import partial


class ViewService(rpc.ViewServiceServicer):
    many_spheres : mb_scene.ManySpheres = None
    active_spot_id = None
    active_spot_id_queue = queue.Queue()

    def __init__(self, many_spheres):
        self.many_spheres = many_spheres
        callback = self.active_object_changed_callback
        subscribe_to_active_object_change_event(self, callback)

    def addMovingSpot(self, request, context):
        mb_utils.run_in_main_thread(
            partial(self.many_spheres.add_moving_spot, request))
        return pb.Empty()

    def setSpotColors(self, request, context):
        mb_utils.run_in_main_thread(
            partial(self.many_spheres.set_spot_colors, request))
        return pb.Empty()

    def setTimePoint(self, request, context):
        mb_utils.run_in_main_thread(
            partial(self.many_spheres.set_time_point, request))
        return pb.Empty()

    def subscribeToActiveSpotChange(self, request, context):
        while context.is_active():
            try:
                spot_id = self.active_spot_id_queue.get(timeout=1)
                if spot_id == None:
                    spot_id = 0xffffffff
                yield pb.ActiveSpotResponse(id=spot_id)
            except queue.Empty:
                pass

    def active_object_changed_callback(self):
        active_spot_id = self.many_spheres.get_active_spot_id()
        if self.active_spot_id != active_spot_id:
            self.active_spot_id = active_spot_id
            self.active_spot_id_queue.put(active_spot_id)

    def setActiveSpot(self, request, context):
        mb_utils.run_in_main_thread(
            partial(self.many_spheres.set_active_spot_id, request))
        return pb.Empty()

    def getTimePoint(self, request, context):
        timepoint = bpy.context.scene.frame_current
        return pb.TimePointResponse(timePoint=timepoint)


def subscribe_to_active_object_change_event(owner, callback):
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.LayerObjects, 'active'),
        owner=owner,
        args=(callback,),
        notify=lambda x: x()
    )


class MastodonBlenderServer:
    many_spheres = None

    def __init__(self):
        self.many_spheres = mb_scene.ManySpheres()
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        greeter = ViewService(self.many_spheres)
        rpc.add_ViewServiceServicer_to_server(greeter, self.server)
        self.server.add_insecure_port('[::]:50051')
        self.server.start()

    def stop(self):
        self.server.stop(grace=2)


mastodon_blender_server = None


def register():
    bpy.app.timers.register(delayed_start_server, first_interval=1)


def delayed_start_server():
    global mastodon_blender_server
    mastodon_blender_server = MastodonBlenderServer()


def unregister():
    global mastodon_blender_server
    if mastodon_blender_server is not None:
        mastodon_blender_server.stop()
        mastodon_blender_server = None