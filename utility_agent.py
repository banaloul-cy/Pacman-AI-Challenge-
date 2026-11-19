
from collections import deque
from game import DIRECTIONS, GHOST_INTERVAL


# Must match MOVE_INTERVAL in main.py.
PACMAN_MOVE_INTERVAL = 220


class UtilityBasedAgent:
    """
    Utility-Based Rational Agent.

    The agent evaluates every legal action using:

    1. Food and power pellet rewards
    2. BFS shortest-path distances
    3. Active ghost danger
    4. Remaining power duration
    5. Ghost hunting while powered
    6. Movement cost
    7. Revisited-position penalties

    The action with the highest utility is selected.
    """

    def __init__(self):

        # ==================================================
        # UTILITY WEIGHTS
        # ==================================================

        self.food_weight = 90.0
        self.power_weight = 100.0
        self.danger_weight = 250.0
        self.hunt_weight = 120.0
        self.move_weight = 1.0
        self.revisit_weight = 3.0

        self.visits = {}
        self.last_decision = {}
        self.move_count = 0

    # ======================================================
    # RESET AGENT MEMORY
    # ======================================================

    def reset(self):

        self.visits.clear()
        self.last_decision = {}
        self.move_count = 0

    # ======================================================
    # ACTIVE GHOSTS
    # ======================================================

    def get_active_ghosts(self, game):
        """
        Return only ghosts that are currently active.

        Captured ghosts waiting for respawn are excluded
        from danger and hunting calculations.
        """

        timers = getattr(
            game,
            "ghost_respawn_timers",
            None
        )

        if timers is None:
            return list(game.ghosts)

        active_ghosts = []

        for i, ghost in enumerate(game.ghosts):

            if (
                i < len(timers)
                and timers[i] > 0
            ):
                continue

            active_ghosts.append(ghost)

        return active_ghosts

    # ======================================================
    # BFS - SHORTEST PATH DISTANCES
    # ======================================================

    def bfs_distances(self, game, start):

        distances = {start: 0}
        queue = deque([start])

        while queue:

            current = queue.popleft()

            for dx, dy in DIRECTIONS:

                neighbor = (
                    current[0] + dx,
                    current[1] + dy
                )

                if not game.can_move(neighbor):
                    continue

                if neighbor in distances:
                    continue

                distances[neighbor] = (
                    distances[current] + 1
                )

                queue.append(neighbor)

        return distances

    # ======================================================
    # TARGET UTILITY
    # ======================================================

    def target_utility(
        self,
        game,
        position,
        distances,
        active_ghosts
    ):

        best_value = float("-inf")
        best_target = None
        best_type = "NONE"

        # ----------------------------------------------
        # NORMAL FOOD
        # ----------------------------------------------

        for food in game.pellets:

            distance = distances.get(food)

            if distance is None:
                continue

            value = (
                self.food_weight / (distance + 1)
            )

            if value > best_value:

                best_value = value
                best_target = food
                best_type = "FOOD"

        # ----------------------------------------------
        # POWER PELLETS
        # ----------------------------------------------

        for power in game.power_pellets:

            distance = distances.get(power)

            if distance is None:
                continue

            nearest_ghost = min(
                (
                    abs(position[0] - ghost[0])
                    + abs(position[1] - ghost[1])
                    for ghost in active_ghosts
                ),
                default=100
            )

            danger_bonus = 0.0

            if (
                nearest_ghost <= 5
                and game.power_timer <= 0
            ):
                danger_bonus = 70.0

            value = (
                self.power_weight + danger_bonus
            ) / (distance + 1)

            if value > best_value:

                best_value = value
                best_target = power
                best_type = "POWER"

        return (
            best_value,
            best_target,
            best_type
        )

    # ======================================================
    # GHOST UTILITY
    # ======================================================

    def ghost_utility(
        self,
        game,
        position,
        distances,
        active_ghosts
    ):

        if not active_ghosts:
            return 0.0

        ghost_distances = [
            distances.get(ghost, 999)
            for ghost in active_ghosts
        ]

        nearest = min(ghost_distances)

        # ----------------------------------------------
        # POWER MODE
        # ----------------------------------------------

        if game.power_timer > 0:

            # Number of Pacman movement opportunities
            # remaining before power expires.
            remaining_steps = (
                game.power_timer
                / PACMAN_MOVE_INTERVAL
            )

            # Allow a small safety margin.
            if nearest + 1 < remaining_steps:

                return (
                    self.hunt_weight
                    / (nearest + 1)
                )

            # Avoid dangerous last-second hunting.
            return 0.0

        # ----------------------------------------------
        # NORMAL MODE
        # ----------------------------------------------

        if nearest == 0:
            return -100000.0

        if nearest == 1:
            return -self.danger_weight

        if nearest == 2:
            return -self.danger_weight * 0.55

        if nearest == 3:
            return -self.danger_weight * 0.22

        return 0.0

    # ======================================================
    # EVALUATE ONE ACTION
    # ======================================================

    def evaluate_action(self, game, action):

        dx, dy = action

        next_position = (
            game.player[0] + dx,
            game.player[1] + dy
        )

        # Walls and invalid movements are forbidden.
        if not game.can_move(next_position):
            return None

        # BFS from the candidate next position.
        distances = self.bfs_distances(
            game,
            next_position
        )

        active_ghosts = self.get_active_ghosts(game)

        # ----------------------------------------------
        # FOOD / POWER UTILITY
        # ----------------------------------------------

        (
            food_value,
            target,
            target_type
        ) = self.target_utility(
            game,
            next_position,
            distances,
            active_ghosts
        )

        if food_value == float("-inf"):
            food_value = 0.0

        # ----------------------------------------------
        # GHOST UTILITY
        # ----------------------------------------------

        ghost_value = self.ghost_utility(
            game,
            next_position,
            distances,
            active_ghosts
        )

        # ----------------------------------------------
        # IMMEDIATE REWARDS
        # ----------------------------------------------

        immediate_reward = 0.0

        if next_position in game.pellets:
            immediate_reward += 10.0

        if next_position in game.power_pellets:
            immediate_reward += 30.0

        # ----------------------------------------------
        # REVISIT PENALTY
        # ----------------------------------------------

        visits = self.visits.get(
            next_position,
            0
        )

        revisit_penalty = (
            min(visits, 10)
            * self.revisit_weight
        )

        # Discourage immediate backtracking.
        if (
            self.last_decision.get(
                "previous_position"
            ) == next_position
        ):
            revisit_penalty += 8.0

        # ----------------------------------------------
        # MOVEMENT COST
        # ----------------------------------------------

        movement_cost = self.move_weight

        # ----------------------------------------------
        # TOTAL UTILITY
        # ----------------------------------------------

        utility = (
            food_value
            + ghost_value
            + immediate_reward
            - movement_cost
            - revisit_penalty
        )

        return {
            "action": action,
            "position": next_position,
            "utility": utility,
            "food_utility": food_value,
            "ghost_utility": ghost_value,
            "immediate_reward": immediate_reward,
            "movement_cost": movement_cost,
            "revisit_penalty": revisit_penalty,
            "target": target,
            "target_type": target_type
        }

    # ======================================================
    # SELECT BEST ACTION
    # ======================================================

    def choose_action(self, game):

        if (
            game.status != "playing"
            or game.paused
        ):
            return None

        evaluations = []

        # Evaluate all four cardinal directions.
        for action in DIRECTIONS:

            result = self.evaluate_action(
                game,
                action
            )

            if result is not None:
                evaluations.append(result)

        if not evaluations:
            return None

        # Select the legal action with maximum utility.
        best = max(
            evaluations,
            key=lambda result: result["utility"]
        )

        previous_position = game.player

        self.last_decision = {
            **best,
            "previous_position": previous_position,
            "evaluations": evaluations
        }

        self.visits[best["position"]] = (
            self.visits.get(
                best["position"],
                0
            ) + 1
        )

        self.move_count += 1

        return best["action"]

    # ======================================================
    # AI DECISION PANEL
    # ======================================================

    def get_decision_info(self):

        if not self.last_decision:

            return {
                "direction": "WAITING",
                "utility": 0.0,
                "target": "NONE",
                "risk": 0.0
            }

        action = self.last_decision["action"]

        names = {
            (1, 0): "RIGHT",
            (-1, 0): "LEFT",
            (0, -1): "UP",
            (0, 1): "DOWN"
        }

        return {
            "direction": names.get(
                action,
                "UNKNOWN"
            ),
            "utility": self.last_decision[
                "utility"
            ],
            "target": self.last_decision[
                "target_type"
            ],
            "risk": self.last_decision[
                "ghost_utility"
            ]
        }
