import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from wallasAPI.router import AIRouter
    from wallasAPI.config import FREE
    print(f"FREE value: {FREE}")
    router = AIRouter()
    print("AIRouter instance created successfully.")
    # Test sort logic which uses FREE
    models = router._get_ordered_model_list()
    print(f"Found {len(models)} models.")
except Exception as e:
    print(f"Error during test: {e}")
    import traceback
    traceback.print_exc()
