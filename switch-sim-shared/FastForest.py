class FastForest:
    """
    A lightweight, pure-Python implementation of a Random Forest.
    It extracts the decision logic from a Scikit-Learn model and runs inference
    using simple if/else statements, avoiding the heavy overhead of numpy/sklearn 
    during the simulation loop.
    """
    def __init__(self, sklearn_model):
        """
        Extracts the raw arrays from the sklearn model into simple Python lists.
        """
        self.trees = []
        
        # Loop through every tree (estimator) in the random forest
        for estimator in sklearn_model.estimators_:
            tree_structure = estimator.tree_
            
            # We extract key arrays for each tree
            # 1. feature: The feature index to check at each node (0, 1, 2, or 3)
            # 2. threshold: The value to compare against
            # 3. children_left/right: The indices of child nodes
            # 4. value: The final vote at leaf nodes
            
            tree_data = {
                'feature': tree_structure.feature.tolist(),
                'threshold': tree_structure.threshold.tolist(),
                'children_left': tree_structure.children_left.tolist(),
                'children_right': tree_structure.children_right.tolist(),
                'value': tree_structure.value.tolist()
            }
            self.trees.append(tree_data)

    def predict(self, f0, f1, f2, f3):
        """
        Runs the decision path for a single item.
        
        Args:
            f0 (float): Current Queue Length
            f1 (float): Shared Buffer Occupancy
            f2 (float): Average Queue Length (EWMA)
            f3 (float): Average Shared Occupancy (EWMA)
            
        Returns:
            int: 0 for ACCEPT, 1 for DROP
        """
        votes_for_drop = 0
        total_trees = len(self.trees)
        
        # Ask every tree for its opinion
        for tree in self.trees:
            node = 0  # Start at the root (node 0)
            
            # Traverse until we hit a leaf node
            # In sklearn's tree structure, a node is a leaf if children_left is -1
            while tree['children_left'][node] != -1:
                
                # Identify which feature this node checks
                feature_idx = tree['feature'][node]
                
                # Map index to the actual input value
                # (Hardcoded if/else is faster than list lookup here)
                if feature_idx == 0:
                    val = f0
                elif feature_idx == 1:
                    val = f1
                elif feature_idx == 2:
                    val = f2
                else:
                    val = f3
                
                # Make the decision: Go Left or Right?
                if val <= tree['threshold'][node]:
                    node = tree['children_left'][node]
                else:
                    node = tree['children_right'][node]
            
            # We are at a leaf node. Check the vote.
            # 'value' looks like [[count_accept, count_drop]]
            # Index 1 is the positive class (Drop) based on your training labels
            counts = tree['value'][node][0]
            
            if counts[1] > counts[0]:
                votes_for_drop += 1
        
        # Majority Vote
        if votes_for_drop > (total_trees / 2):
            return 1  # DROP
        else:
            return 0  # ACCEPT