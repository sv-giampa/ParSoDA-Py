import os
import shutil
from .test_runtime import TestRuntime
    
class PySparkDev(TestRuntime):    
    def run(self, app, chunk_size, cores, log_file_path) -> int:
        # create archive for making sources available to spark
        shutil.make_archive("parsoda_src", 'zip', "parsoda")
        exit_code = os.system(
            f"spark-submit "
            f"--driver-memory 1G "
            #f"--master \"spark://spark-master:7077\" "
            #f"--executor-memory {mem}M "
            #f"--conf \"spark.memory.fraction=0.3\" "
            #"--conf \"spark.driver.extraJavaOptions=-Xss512M\" "
            #f"--conf \"spark.dynamicAllocation.enabled=true\" " 
            #f"--conf \"spark.dynamicAllocation.executorIdleTimeout=120m\" " 
            f"--conf \"spark.network.timeout=10000000\" " 
            f"--conf \"spark.executor.heartbeatInterval=1000000\" " 
            #f"--conf \"spark.rpc.message.maxSize=2047\" "
            #f"--conf \"spark.rpc.io.serverThreads=64\" "
            f"--conf \"spark.executor.extraJavaOptions=-XX:ThreadStackSize=2048\" "
            #f"--executor-cores {cores/nodes}"
            #f"--num-executors {cores} "
            f"--total-executor-cores {cores} "
            f"--py-files ./parsoda_src.zip "
            f"{app} pyspark --chunk-size {chunk_size} "
            f"> {log_file_path}"
        )
        os.remove("parsoda_src.zip")
        return exit_code
    
class PySparkScalab(TestRuntime):    
    def run(self, app, chunk_size, cores, log_file_path) -> int:
        # create archive for making sources available to spark
        shutil.make_archive("parsoda_src", 'zip', "parsoda")
        exit_code = os.system(
            f"spark-submit "
            f"--driver-memory 200G "
            f"--master \"spark://spark-master:7077\" "
            #f"--executor-memory {mem}M "
            #f"--conf \"spark.memory.fraction=0.3\" "
            #"--conf \"spark.driver.extraJavaOptions=-Xss512M\" "
            #f"--conf \"spark.dynamicAllocation.enabled=true\" " 
            #f"--conf \"spark.dynamicAllocation.executorIdleTimeout=120m\" " 
            f"--conf \"spark.network.timeout=10000000\" " 
            f"--conf \"spark.executor.heartbeatInterval=1000000\" " 
            #f"--conf \"spark.rpc.message.maxSize=2047\" "
            #f"--conf \"spark.rpc.io.serverThreads=64\" "
            f"--conf \"spark.executor.extraJavaOptions=-XX:ThreadStackSize=2048\" "
            #f"--executor-cores {cores/nodes}"
            #f"--num-executors {cores} "
            f"--total-executor-cores {cores} "
            f"--py-files ./parsoda_src.zip "
            f"{app} pyspark --chunk-size {chunk_size} "
            f"> {log_file_path}"
        )
        os.remove("parsoda_src.zip")
        return exit_code