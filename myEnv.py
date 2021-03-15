# import the base environment class
from flow.envs import Env
from gym.spaces.box import Box
import numpy as np

ADDITIONAL_ENV_PARAMS = {
    "max_accel": 1,
    "max_decel": 1,
}

# define the environment class, and inherit properties from the base environment class
class myEnv(Env):
    pass

class myEnv(myEnv):

    @property
    def action_space(self):
        num_actions = self.initial_vehicles.num_rl_vehicles
        accel_ub = self.env_params.additional_params["max_accel"]
        accel_lb = - abs(self.env_params.additional_params["max_decel"])

        return Box(low=accel_lb,
                   high=accel_ub,
                   shape=(num_actions,))
   
    @property
    def observation_space(self):
        print("Shape should be:", 3*self.initial_vehicles.num_vehicles)
        print("Shape should be:", 3*self.initial_vehicles.num_vehicles)
        print("Shape should be:", 3*self.initial_vehicles.num_vehicles)
        
        return Box(
            low=(float("inf")*-1),
            high=float("inf"),
            shape=(3*self.initial_vehicles.num_vehicles,),
        )
    
    def get_distance_to_intersection(self, veh_ids):
        """Determine the distance from a vehicle to its next intersection.
        Parameters
        ----------
        veh_ids : str or str list
            vehicle(s) identifier(s)
        Returns
        -------
        float (or float list)
            distance to closest intersection
        """
        if isinstance(veh_ids, list):
            return [self.get_distance_to_intersection(veh_id)
                    for veh_id in veh_ids]
        return self.find_intersection_dist(veh_ids)

    def find_intersection_dist(self, veh_id):
        """Return distance from intersection.
        Return the distance from the vehicle's current position to the position
        of the node it is heading toward.
        """
        edge_id = self.k.vehicle.get_edge(veh_id)
        # FIXME this might not be the best way of handling this
        if edge_id == "":
            return -10
        if 'center' in edge_id:
            return 0
        edge_len = self.k.network.edge_length(edge_id)
        relative_pos = self.k.vehicle.get_position(veh_id)
        dist = edge_len - relative_pos
        return dist
    
    def _apply_rl_actions(self, rl_actions):
        
#         print("rl actions", rl_actions)
        
        # the names of all autonomous (RL) vehicles in the network
        rl_ids = self.k.vehicle.get_rl_ids()
        
#         print("rl ids", rl_ids)

        # use the base environment method to convert actions into accelerations for the rl vehicles
        self.k.vehicle.apply_acceleration(rl_ids, rl_actions)
    
    def _convert_edge(self, edge):
        _dict = {"exit_edge1" : 5,"enter_edge2" : 2,"enter_edge3" : 3,"exit_edge4" : 8,"enter_edge1":1,"exit_edge2" : 6,"exit_edge3" : 7, "enter_edge4" : 4}
        
        convertedEdge = _dict[edge] - 1
        
        return convertedEdge
        
    
    def get_state(self, **kwargs):
        max_dist = 200
        num_edges = 8
        
        speeds = [
            self.k.vehicle.get_speed(veh_id) / self.k.network.max_speed()
            for veh_id in self.k.vehicle.get_ids()
        ]
        dist_to_intersec = [
            self.get_distance_to_intersection(veh_id) / max_dist
            for veh_id in self.k.vehicle.get_ids()
        ]
        edges = [
            self._convert_edge(self.k.vehicle.get_edge(veh_id)) /
            (num_edges - 1)
            for veh_id in self.k.vehicle.get_ids()
        ]
        while len(speeds) != 32:
            speeds.append(0)
            
        while len(dist_to_intersec) != 32:
            dist_to_intersec.append(1)
            
        while len(edges) != 32:
            edges.append(-1)
            
        result = []
        
        resultLst = [speeds, dist_to_intersec, edges]
        
        for r in resultLst:
            result += r
            
        result = np.array(result)
        
        print("EEEEEEEEEEEEEE", result.shape)
        
        return result
    
    def compute_reward(self, rl_actions, **kwargs):
        
#       print("Compute Reward")
        
        # the get_ids() method is used to get the names of all vehicles in the network
        ids = self.k.vehicle.get_ids()

        # we next get a list of the speeds of all vehicles in the network
        speeds = self.k.vehicle.get_speed(ids)

        # finally, we return the average of all these speeds as the reward
        
        result = np.mean(speeds)
        
        print("Average Speed#@#@#@#@#@#@#@#@#@#@#@", result)
        
        print("Maximum Speed#@#@#@#@#@#@#@#@#@#@#@", np.max(speeds))
        
        return result
    
    def additional_command(self):
        
#         print("Respawn Command")
        
        """See parent class.
        Used to insert vehicles that are on the exit edge and place them
        back on their entrance edge.
        """
        
        count = 0
        
        for veh_id in self.k.vehicle.get_ids():
            if (self._reroute_if_final_edge(veh_id)):
                count += 1
                
        print("Count &*&*&*&*&*&*&*&*&*&*&*&*&*&", count)
            
#         print("Vehicles IDs", self.k.vehicle.get_ids())
            
#         print(str(len(self.k.vehicle.get_ids())) + "Length of vehicle ids")

    def _reroute_if_final_edge(self, veh_id):
        """Reroute vehicle associated with veh_id.
        Checks if an edge is the final edge. If it is return the route it
        should start off at.
        """
        edge = self.k.vehicle.get_edge(veh_id)
        
#         print(str(edge) + " edge")
#         print(str(veh_id) + " vehicle id")
        
        route_id = None
        
        if edge.startswith("exit"):
#             print("This car will exit")
            temp = str(edge)[4:]
            newedgeid = "enter" + temp
            
            route_id = newedgeid
            
#             print ("This car will go to " + newedgeid)
                
#         if edge == "":
#             return
#         if edge[0] == ":":  # center edge
#             return
#         pattern = re.compile(r"[a-zA-Z]+")
#         edge_type = pattern.match(edge).group()
#         edge = edge.split(edge_type)[1].split('_')
#         row_index, col_index = [int(x) for x in edge]

#         # find the route that we're going to place the vehicle on if we are
#         # going to remove it
#         route_id = None
#         if edge_type == 'bot' and col_index == self.cols:
#             route_id = "bot{}_0".format(row_index)
#         elif edge_type == 'top' and col_index == 0:
#             route_id = "top{}_{}".format(row_index, self.cols)
#         elif edge_type == 'left' and row_index == 0:
#             route_id = "left{}_{}".format(self.rows, col_index)
#         elif edge_type == 'right' and row_index == self.rows:
#             route_id = "right0_{}".format(col_index)

        if route_id is not None:
        
#             print("Route ID is NOT None" + str(veh_id) + str(route_id))
        
            type_id = self.k.vehicle.get_type(veh_id)
            lane_index = self.k.vehicle.get_lane(veh_id)
            
#             print(str(len(self.k.vehicle.get_ids())) + "Length of vehicle ids BEFORE REMOVE")
            
            # remove the vehicle
            self.k.vehicle.remove(veh_id)
            
#             print("Vehicle ID", veh_id)
#             print("Edge", route_id)
#             print("Type ID", type_id)
#             print("Lane", lane_index)
#             print("Lane: "+str(lane_index))
            # reintroduce it at the start of the network
            self.k.vehicle.add(
                veh_id=veh_id,
                edge=route_id,
                type_id=str(type_id),
 #               lane=str(lane_index),
                lane="random",
                pos="0",
                speed="max")
        
            return True
            
#             print(self.k.vehicle)
            
#             print(str(len(self.k.vehicle.get_ids())) + "Length of vehicle ids AFTER ADD")

        return False