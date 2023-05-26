import json

import pandas as pd
import matplotlib.pyplot as plt

Z_MIN = 285
Z_MAX = 421

class ProcessGameState:

    def __init__(self, filepath):
        # Read the parquet file with engine pyarrow and store the data in format of dataFrame
        self.data = pd.read_parquet("/Users/zhangshanrong/Desktop/game_state_frame_data.parquet", engine='pyarrow')

    def show_the_data(self, num_rows):
        # show the first num of the data
        return self.data.head(num_rows)

    def is_point_in_triangle(pt, v1, v2, v3):
        # Barycentric technique
        alpha = ((v2[1] - v3[1]) * (pt[0] - v3[0]) + (v3[0] - v2[0]) * (pt[1] - v3[1])) / (
                    (v2[1] - v3[1]) * (v1[0] - v3[0]) + (v3[0] - v2[0]) * (v1[1] - v3[1]))
        beta = ((v3[1] - v1[1]) * (pt[0] - v3[0]) + (v1[0] - v3[0]) * (pt[1] - v3[1])) / (
                    (v2[1] - v3[1]) * (v1[0] - v3[0]) + (v3[0] - v2[0]) * (v1[1] - v3[1]))
        gamma = 1.0 - alpha - beta
        return alpha > 0 and beta > 0 and gamma > 0

    def is_point_in_quadrilateral(pt, v1, v2, v3, v4):
        # For a point to be in a quadrilateral, it has to be in one of the two triangles that make up the quadrilateral
        return ProcessGameState.is_point_in_triangle(pt, v1, v2, v3) \
            or ProcessGameState.is_point_in_triangle(pt, v1, v3, v4)

    def is_point_on_line(pt, v1, v2):
        if pt == v1 or pt == v2:
            return False

        # Calculate slope of the line
        m = (v1[1] - v2[1]) / (v1[0] - v2[0])

        # Calculate y-coordinate of the point if it was on the line
        y = m * (pt[0] - v1[0]) + v1[1]

        # Return True if the actual y-coordinate is close enough to the calculated y-coordinate
        return abs(y - pt[1]) < 1e-6

    def is_within_boundary(self, z_min, z_max):
        # Define triangle and quadrilateral coordinates
        tri_coords = [(-1735, 250), (-2024, 398), (-1565, 580)]  # Points 13, 14, 17
        quad_coords = [(-2024, 398), (-2806, 742), (-2472, 1233), (-1565, 580)]  # Points 14, 15, 16, 17
        line_coords = [(-2024, 398), (-1565, 580)]  # Points 14, 17
        # Apply the checks to each row
        within_boundary = self.data.apply(lambda row: (z_min <= row['z'] <= z_max) and \
                        (ProcessGameState.is_point_in_quadrilateral((row['x'], row['y']),*quad_coords) or \
                        ProcessGameState.is_point_in_triangle((row['x'], row['y']),*tri_coords) or \
                        ProcessGameState.is_point_on_line((row['x'], row['y']),*line_coords)), axis=1)
        return within_boundary


    def add_boundary_check_column(self, Z_MIN, Z_MAX):
        self.data['within_boundary'] = self.is_within_boundary(Z_MIN, Z_MAX)

    def extract_weapon_classes(self):
        def get_weapon_classes(inventory):
            # If inventory is not None
            if inventory is not None:
                weapon_classes = []
                # Iterate over each item in inventory
                for item in inventory:
                    # If 'weapon_class' is in the dictionary item, append it to weapon_classes
                    if 'weapon_class' in item:
                        weapon_classes.append(item['weapon_class'])
                return weapon_classes
            else:
                return None

        # Apply the function to each row in the 'inventory' column
        self.data['weapon_classes'] = self.data['inventory'].apply(get_weapon_classes)

    def plot_player_movements(self, round_num, team):
        # Filter the data for the specific round and team
        round_data = self.data[(self.data['round_num'] == round_num) & (self.data['team'] == team)]

        # Get the unique players
        players = round_data['player'].unique()

        # Create a new figure
        plt.figure(figsize=(10, 10))

        # For each player
        for player in players:
            # Get the data for this player
            player_data = round_data[round_data['player'] == player]

            # Plot the player's movements
            plt.scatter(player_data['x'], player_data['y'], label=player)

        # Set the title, labels, and legend
        plt.title(f'Player movements in round {round_num} for {team}')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.legend()
        # Set x-axis range
        plt.xlim(-4500, 0)
        # Set y-axis range
        plt.ylim(-4000, 1500)
        # Show the plot
        plt.savefig(f'/Users/zhangshanrong/Desktop/Team2/player_movements{round_num}.png')
        plt.close()

    def extract_specific_players(self, team, round_num, players):
        # Filter the data
        data_filtered = self.data[(self.data['team'] == team) & (self.data['round_num'] == round_num) & (self.data['player'].isin(players))]

        # Select the columns x, y, z and within_boundary
        data_selected = data_filtered[['x', 'y', 'z', 'within_boundary']]

        return data_selected

    def count_players_within_boundary(self, team, side):
        # Filter the data
        data_filtered = self.data[(self.data['team'] == team) & (self.data['side'] == side)]

        data_grouped = data_filtered.groupby(['round_num', 'player'])
        players_within_boundary = data_grouped['within_boundary'].any()

        # For each round, count the number of players who ever entered the boundary
        players_within_boundary_per_round = players_within_boundary.groupby(level=0).sum()

        return players_within_boundary_per_round


a = ProcessGameState("/Users/zhangshanrong/Desktop/game_state_frame_data.parquet")
a.add_boundary_check_column(Z_MIN,Z_MAX)
c = a.count_players_within_boundary("Team2", "T")
print(c)


#team2_players_within_boundary = count_players_within_boundary(a.data, 'Team2', 'T')
#print(team2_players_within_boundary)
"""for i in range(1,31):
    a.plot_player_movements(i, 'Team2')"""
# filtered_data = a.data[a.data['inventory'].notna()]
# c = a.is_within_boundary(Z_MIN, Z_MAX)
#a.extract_weapon_classes()


#a.data.to_excel("/Users/zhangshanrong/Desktop/1.xlsx", engine='openpyxl', index=False)
#print(a['weapon_classes'].head())
