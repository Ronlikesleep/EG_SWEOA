import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import gaussian_kde
import numpy as np

# Define z-axis boundaries of the chokepoint
Z_MIN = 285
Z_MAX = 421

class ProcessGameState:

    def __init__(self, filepath):
        #Q1 a
        # Read the parquet file with engine pyarrow and store the data in format of dataFrame
        self.data = pd.read_parquet(filepath, engine='pyarrow')

    def show_the_data(self, num_rows):
        # show the first num of the data
        return print(self.data.head(num_rows))

    @staticmethod
    def is_point_in_triangle(pt, v1, v2, v3):
        # Check if point is inside triangle using barycentric technique
        # For a point to be inside, all alpha, beta, gamma need to be positive
        alpha = ((v2[1] - v3[1]) * (pt[0] - v3[0]) + (v3[0] - v2[0]) * (pt[1] - v3[1])) / (
                    (v2[1] - v3[1]) * (v1[0] - v3[0]) + (v3[0] - v2[0]) * (v1[1] - v3[1]))
        beta = ((v3[1] - v1[1]) * (pt[0] - v3[0]) + (v1[0] - v3[0]) * (pt[1] - v3[1])) / (
                    (v2[1] - v3[1]) * (v1[0] - v3[0]) + (v3[0] - v2[0]) * (v1[1] - v3[1]))
        gamma = 1.0 - alpha - beta
        return alpha > 0 and beta > 0 and gamma > 0

    @staticmethod
    def is_point_in_quadrilateral(pt, v1, v2, v3, v4):
        # For a point to be in a quadrilateral, it has to be in one of the two triangles that make up the quadrilateral
        return ProcessGameState.is_point_in_triangle(pt, v1, v2, v3) \
            or ProcessGameState.is_point_in_triangle(pt, v1, v3, v4)

    @staticmethod
    def is_point_on_line(pt, v1, v2):
        # A point is on a line if the line's y-coordinate at the point's x-coordinate is approximately equal to the point's y-coordinate
        # this function is used to find the points between the diagonal of quadrilateral should be considered as within the boundary
        if pt == v1 or pt == v2:
            return False

        # Calculate slope of the line
        m = (v1[1] - v2[1]) / (v1[0] - v2[0])

        # Calculate y-coordinate of the point if it was on the line
        y = m * (pt[0] - v1[0]) + v1[1]

        # Return True if the actual y-coordinate is close enough to the calculated y-coordinate
        return abs(y - pt[1]) < 1e-6

    def is_within_boundary(self, z_min, z_max):
        # Q1 b
        # Define triangle, quadrilateral and the diagonal coordinates
        # the overall time complexity of is_within_boundary is O(n) and only use the standard Python libraries
        # returns a pandas.Series object, which contains Boolean values
        # indicating whether each row of the dataframe is within the boundary.
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
        # Add a new boolean column to the dataframe that indicates whether each row is within boundary
        self.data['within_boundary'] = self.is_within_boundary(Z_MIN, Z_MAX)

    def extract_weapon_classes(self):
        # Q1 c
        # Extract weapon classes from inventory
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
        # Add a new column called 'weapon_classes', each column is a list
        self.data['weapon_classes'] = self.data['inventory'].apply(get_weapon_classes)

    def plot_player_movements(self, round_num, team):
        # This is a helper function to track the movement of each team
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

        # Set x-axis y-axis range and obtain a concise overview of the movement that aligns with the map
        plt.xlim(-4500, 0)
        plt.ylim(-4000, 1500)

        # Show the plot
        plt.savefig(f'/Users/zhangshanrong/Desktop/Team2/player_movements{round_num}.png')
        plt.close()

    def count_players_within_boundary_each_round(self, team, side):
        # Q2 a
        # This function calculates the number of players of a specific team and side who enter the boundary in each round.
        # Filter the data
        data_filtered = self.data[(self.data['team'] == team) & (self.data['side'] == side)]

        data_grouped = data_filtered.groupby(['round_num', 'player'])
        players_within_boundary = data_grouped['within_boundary'].any()

        # For each round, count the number of players who ever entered the boundary
        players_within_boundary_per_round = players_within_boundary.groupby(level=0).sum()

        return players_within_boundary_per_round


    def get_first_two_entry_rows(self):
        # Retrieve the whole row for the first two entry per round of Team2 on the T side
        # where the player enters BombsiteB with a rifle or an SMG(but SMG only for CT)
        # Filter the data for Team2 on the T side
        team2_data = self.data[(self.data['team'] == 'Team2') & (self.data['side'] == 'T') &
                               (self.data['weapon_classes'].notna())]

        # Initialize a DataFrame to store the first two entry rows
        first_two_entry_rows = pd.DataFrame()

        # Iterate over each round
        for round_num in team2_data['round_num'].unique():
            # Filter the data for the current round and players who entered BombsiteB
            round_data = team2_data[(team2_data['round_num'] == round_num) & (team2_data['area_name'] == 'BombsiteB')]

            # Filter the data for players who entered BombsiteB with at least one rifle or SMG
            round_entry_data = round_data[
                round_data['weapon_classes'].apply(lambda x: any(weapon in ['Rifle', 'SMG'] for weapon in x))
            ]
            if not round_entry_data.empty:
                # Keep only the first entry for each player
                round_entry_data = round_entry_data.sort_values(by='tick').drop_duplicates(subset='player')
                # Check if there are at least two distinct players that satisfy the condition
                if round_entry_data.shape[0] >= 2:
                    # Append the first two entries
                    first_two_entries = round_entry_data.iloc[:2]
                    first_two_entry_rows = pd.concat([first_two_entry_rows, pd.DataFrame(first_two_entries)], ignore_index=True)

        return first_two_entry_rows

    def get_average_timer(self):
        # Q2 b
        # Since the 'seconds' and 'clock_time' can be set, I will use tick to calculate the timer
        # calculate each round's start ticks
        def calculate_round_start_ticks(df):
            return df.groupby('round_num')['tick'].min()

        first_two_entry_rows = self.get_first_two_entry_rows()
        # Group by round_num and calculate the average tick for each round
        average_ticks = first_two_entry_rows.groupby('round_num')['tick'].mean()
        round_start_ticks = calculate_round_start_ticks(self.data)

        # Subtract the round start tick from the average tick for each round
        timer_ticks = average_ticks - round_start_ticks.loc[average_ticks.index]

        # Convert tick to seconds
        timer_seconds = timer_ticks / 128

        # Calculate the average timer over all rounds
        average_timer = timer_seconds.mean()

        return average_timer

    def draw_heatmap(self):
        # Q2 c
        # This function generates a heatmap showing the density of positions of 'Team2' on the 'CT' side in 'BombsiteB'.
        # The function calculates densities and identifies the top five density points overall.
        # The heatmap is sliced along the z-axis, and the top five density points within each slice are highlighted.
        ct_data = self.data[
            (self.data['team'] == 'Team2') & (self.data['side'] == 'CT') & (self.data['area_name'] == 'BombsiteB')]

        # Calculate densities and get overall top five density points
        x = ct_data['x']
        y = ct_data['y']
        z = ct_data['z']
        xy = np.vstack([x, y])
        density = gaussian_kde(xy)(xy)
        idxs_top5_density = np.argsort(density)[-5:]
        top5_density_points = list(zip(x.iloc[idxs_top5_density], y.iloc[idxs_top5_density], z.iloc[idxs_top5_density]))

        # Define z slices
        z_slices = range(int(ct_data['z'].min()), int(ct_data['z'].max()), 100)

        for z in z_slices:
            # Get data in the current slice
            ct_data_slice = ct_data[(ct_data['z'] >= z) & (ct_data['z'] < z + 100)]

            # KDE plot
            plt.figure(figsize=(10, 10))

            # Generate KDE plot
            ax = sns.kdeplot(data=ct_data_slice, x='x', y='y', fill=True, cmap='Reds', levels=100)

            # Mark top five points of maximum density if they fall in the current slice
            for point in top5_density_points:
                if z <= point[2] < z + 100:
                    ax.plot(point[0], point[1], 'bo')

            plt.title(f'Heatmap of Team2 CT Side Positions in BombsiteB for Z slice {z}-{z + 100}')
            plt.show()
        return top5_density_points



