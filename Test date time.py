from datetime import datetime
run_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
print(f"MSF API run at {run_datetime}")

#     print('test if HME shut in df ', df_shuts[df_shuts['MaintenanceShutdown_BK'] =='83321']) 
df_shuts["AssetCode"] = df_shuts["AssetCode"].apply(lambda x: x[0].get("code") if isinstance(x, list) and len(x) > 0 else None
)
