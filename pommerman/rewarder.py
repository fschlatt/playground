import numpy as np


class Rewarder():

    def __init__(self,
                 collect_bomb=0.1,
                 collect_kick=0.1,
                 collect_range=0.1,
                 dead_enemy=0.5,
                 dead_teammate=-0.5,
                 elim_enemy=0.5,
                 elim_teammate=-0.5,
                 explode_crate=0.01,
                 kick_elim=0.5,
                 bomb_offset=True):

        self.collect_bomb = collect_bomb
        self.collect_kick = collect_kick
        self.collect_range = collect_range
        self.dead_enemy = dead_enemy
        self.dead_teammate = dead_teammate
        self.elim_enemy = elim_enemy
        self.explode_crate = explode_crate
        self.elim_teammate = elim_teammate
        self.kick_elim = kick_elim
        self.bomb_offset = bomb_offset

    def __call__(self, rewards, board, prev_board, agents, prev_kick, bombs, flames):
        for idx, agent in enumerate(agents):
            if self.bomb_offset:
                # reward = [[-1, rewards[idx]]]
                reward = [[-1, 0]]
            else:
                # reward = rewards[idx]
                reward = 0
            if not agent.is_alive:
                if self.bomb_offset:
                    reward = [[-1, -1]]
                else:
                    rewards[idx] = -1
                    continue

            if self.collect_bomb:
                reward += self.calc_collect_bomb(
                    agent.position,
                    prev_board)
            if self.collect_kick:
                reward += self.calc_collect_kick(
                    agent.position,
                    prev_board, prev_kick[idx])
            if self.collect_range:
                reward += self.calc_collect_range(
                    agent.position,
                    prev_board)
            if self.dead_enemy:
                reward += self.calc_dead_enemy(
                    agents,
                    [enemy for enemy in agent.enemies],
                    board, prev_board, flames)
            if self.dead_teammate:
                reward += self.calc_dead_teammate(
                    agents,
                    agent.teammate,
                    board, prev_board, flames)
            if self.elim_enemy:
                reward += self.calc_elim_enemy(
                    agent, agents,
                    [enemy for enemy in agent.enemies],
                    board, prev_board, flames)
            if self.elim_teammate:
                reward += self.calc_elim_teammate(
                    agent, agents,
                    agent.teammate,
                    board, prev_board, flames)
            if self.explode_crate:
                reward += self.calc_explode_crate(
                    agent, prev_board, flames)
            if self.kick_elim:
                reward += self.calc_kick_elim(
                    agent, agents,
                    [enemy for enemy in agent.enemies],
                    board, prev_board, flames)
            if self.bomb_offset:
                reward = np.array(reward)
                reward = [[idx, reward[:, 1][reward[:, 0] == idx].sum()]
                        for idx in np.unique(reward[:, 0])]
                reward = np.array(reward)
                reward = reward[np.argsort(reward[:, 0])][::-1]
            rewards[idx] = reward

        return rewards

    def calc_collect_bomb(self, pos, prev_board):
        if prev_board[pos] == 6:
            if self.bomb_offset:
                return [[-1, self.collect_bomb]]
            return self.collect_bomb
        if self.bomb_offset:
            return []
        return 0

    def calc_collect_kick(self, pos, prev_board, kick):
        if (prev_board[pos] == 8) and not kick:
            if self.bomb_offset:
                return [[-1, self.collect_kick]]
            return self.collect_kick
        if self.bomb_offset:
            return []
        return 0

    def calc_collect_range(self, pos, prev_board):
        if prev_board[pos] == 7:
            if self.bomb_offset:
                return [[-1, self.collect_range]]
            return self.collect_range
        if self.bomb_offset:
            return []
        return 0

    def calc_dead_enemy(self, agents, enemies, board, prev_board, flames):
        enemy_dead = sum([
            (prev_board == enemy.value) * int(enemy.value not in board)
            for enemy in enemies])
        enemy_dead = enemy_dead.astype(bool)
        if self.bomb_offset:
            reward = []
        else:
            reward = 0
        if not enemy_dead.any():
            return reward
        dead_enemies = prev_board[enemy_dead]
        enemy_pos = [enemy.position for enemy in agents
                     if enemy.agent_id + 10 in dead_enemies]
        if not self.bomb_offset:
            return self.dead_enemy * len(enemy_pos)
        for pos in enemy_pos:
            for flame in flames:
                if flame.position == pos:
                    reward += [[-(12 - flame.life), self.dead_enemy]]
                    break
        return reward

    def calc_dead_teammate(self, agents, teammate, board, prev_board, flames):
        teammate_dead = (prev_board == teammate) * int(teammate not in board)
        teammate_dead = teammate_dead.astype(bool)
        if self.bomb_offset:
            reward = []
        else:
            reward = 0
        if not teammate_dead.any():
            return reward
        teammate_pos = (None, None)
        for agent in agents:
            if agent.agent_id + 10 == prev_board[teammate_dead]:
                teammate_pos = agent.position
                break
        if not self.bomb_offset:
            return self.dead_teammate
        for flame in flames:
            if flame.position == pos:
                reward += [[-(12 - flame.life), self.dead_teammate]]
                break
        return reward

    def calc_elim_enemy(self, agent, agents, enemies, board, prev_board, flames):
        enemy_dead = sum([
            (prev_board == enemy.value) * int(enemy.value not in board)
            for enemy in enemies])
        enemy_dead = enemy_dead.astype(bool)
        if self.bomb_offset:
            reward = []
        else:
            reward = 0
        if not enemy_dead.any():
            return reward
        dead_enemies = prev_board[enemy_dead]
        enemy_pos = [enemy.position for enemy in agents
                     if enemy.agent_id + 10 in dead_enemies]
        for pos in enemy_pos:
            for flame in flames:
                if agent.agent_id != flame.bomb.bomber.agent_id:
                    continue
                if flame.position == pos:
                    if self.bomb_offset:
                        reward += [[-(12 - flame.life), self.elim_enemy]]
                    if not self.bomb_offset:
                        reward += self.elim_enemy * len(enemy_pos)
                    break
        return reward

    def calc_elim_teammate(self, agent, agents, teammate, board, prev_board, flames):
        teammate_dead = (prev_board == teammate) * int(teammate not in board)
        teammate_dead = teammate_dead.astype(bool)
        if self.bomb_offset:
            reward = []
        else:
            reward = 0
        if not teammate_dead.any():
            return reward
        teammate_pos = (None, None)
        for agent in agents:
            if agent.agent_id + 10 == prev_board[teammate_dead]:
                teammate_pos = agent.position
                break
        for flame in flames:
            if flame.position == pos:
                if agent.agent_id != flame.bomb.bomber.agent_id:
                    continue
                if self.bomb_offset:
                    return [[-(12 - flame.life), self.elim_teammate]]
                if not self.bomb_offset:
                    return self.elim_teammate
                break
        return reward

    def calc_explode_crate(self, agent, prev_board, flames):
        if self.bomb_offset:
            reward = []
        else:
            reward = 0
        prev_board = prev_board.copy()
        for flame in flames:
            if flame.life < 2 or agent.agent_id != flame.bomb.bomber.agent_id:
                continue
            if prev_board[flame.position] == 2:
                if self.bomb_offset:
                    reward += [[-10, self.explode_crate]]
                else:
                    reward += self.explode_crate
                prev_board[flame.position] = 0
        return reward

    def calc_kick_elim(self, agent, agents, enemies, board, prev_board, flames):
        enemy_dead = sum([
            (prev_board == enemy.value) * int(enemy.value not in board)
            for enemy in enemies])
        enemy_dead = enemy_dead.astype(bool)
        if self.bomb_offset:
            reward = []
        else:
            reward = 0
        if not enemy_dead.any():
            return reward
        dead_enemies = prev_board[enemy_dead]
        enemy_pos = [enemy.position for enemy in agents
                     if enemy.agent_id + 10 in dead_enemies]
        for pos in enemy_pos:
            for flame in flames:
                for kicker, kick_offset in flame.bomb.kicks:
                    if agent.agent_id != kicker.agent_id:
                        continue
                    if flame.position == pos:
                        if self.bomb_offset:
                            reward += [[-(kick_offset + 2 - flame.life), self.kick_elim]]
                        if not self.bomb_offset:
                            reward += self.kick_elim * len(enemy_pos)
                        break
        return reward
