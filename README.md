# function-as-a-service-CE7490
Optimising the Serverless Workload at Cloud

## Azure Functions Trace 2019

[Data Source](https://github.com/Azure/AzurePublicDataset/blob/master/AzureFunctionsDataset2019.md)

Histogram may be outdated, we can use forecasted histogram to improve.

## Schema and Description
### Function Invocation Counts
 * 14 files, one file per 24-h period: `invocations_per_function_md.anon.d[01-14].csv`
#### Schema
|Field|Description  |
|--|--|
| HashOwner | unique id of the application owner <sup>1</sup> |
| HashApp | unique id for application name <sup>1</sup> |
| HashFunction | unique id for the function name within the app <sup>1</sup>|
|Trigger | trigger for the function<sup>2</sup>|
|1 .. 1440 | 1440 fields, with the number of invocations of the function per each minute of the 24h period in the file<sup>3</sup>
#### Notes
 1. All ids are hashed using HMAC-SHA256 with secret salts. Each column uses a different salt. These are consistent across the different types of files, so you can correlate onwers, apps, and functions here with those in the duration and memory data. Note that two apps with the same original name under different owners would be hashed to *different* values. Likewise, two functions with the same original name belonging to different apps would be hashed to different values. 
 2. Trigger indicates one of the trigger groups from the paper. Azure Functions has a large number of triggers, see [here](https://docs.microsoft.com/en-us/azure/azure-functions/functions-triggers-bindings) for details. Here, as in the paper, we group triggers of similar types into the 7 following groups:

    * **http** (HTTP)
    * **timer** (Timer) 
    * **event** (Event Hub, Event Grid)
    * **queue** (Service Bus, Queue Storage, RabbitMQ, Kafka, MQTT)
    * **storage** (Blob Storage, CosmosDB, Redis, File)
    * **orchestration** (Durable Functions: activities, orcherstration)
    * **others** (all other triggers)
     

3.  The number of invocations is recorded after the functions execute

### Function Execution Duration
14 files, one file per 24-h period: `function_durations_percentiles.anon.d[01-14].csv`
#### Schema

|Field|Description  |
|--|--|
| HashOwner | unique id of the application owner |
| HashApp | unique id for application name  |
| HashFunction | unique id for the function name within the app | 
|Average | Average execution time (ms) across all invocations of the 24-period <sup>4</sup>|  
|Count | Number of executions used in computing the average<sup>5</sup>|  
|Minimum | Minimum execution time for the 24-hour period<sup>6</sup>|  
|Maximum | Maximum execution time for the 24-hour period<sup>6</sup>|  
|percentile_Average_0| Weighted 0th-percentile of the execution time *average*<sup>7</sup> |  
|percentile_Average_1| Weighted 1st-percentile of the execution time *average*<sup>7</sup> |  
|percentile_Average_25 | Weighted 25th-percentile of the execution time *average*<sup>7</sup>|  
|percentile_Average_50 | Weighted 50th-percentile of the execution time *average*<sup>7</sup>|  
|percentile_Average_75 | Weighted 75th-percentile of the execution time *average*<sup>7</sup>|  
|percentile_Average_99 | Weighted 99th-percentile of the execution time *average*<sup>7</sup>|  
|percentile_Average_100 | Weighted 100th-percentile of the execution time *average*<sup>7</sup>|

#### Notes
4. Execution time is in milliseconds and **does not** include the cold start time
5. While the number here is very close to the sum of the invocations in the 
   invocations_per_minute files, sometimes it is different. These two numbers are taken from different logs, and in a few rare cases they may diverge (even by a lot). Use the number here only to operate on or reason about the values in this table (e.g., to compose averages across 24-hour periods).
6. Min and Max are the true minimum and maximum. There are a few cases in which these values were not recorded in this dataset, because of a field naming issue in a few versions of the Azure Functions runtime.
7. These require an explanation, as we could not log the duration of every invocation. Every 30 seconds, the framework records, for each function, the number of invocations *i*, the minimum, average, and maximum execution times over these *i* invocations. The percentiles in this table are not of the invocation times, but of their averages. Suppose there are two periods with averages 10 and 12 over, respectively, 5 and 3 invocations. The percentiles are computed on the "weighted" distribution (10,10,10,10,12,12,12). If the number of samples over each 30-second interval is small, these percentiles over the average will tend to the percentiles of the true distribution.

### Application Memory
12 files, one file per 24-h period (last 2 are missing): `app_memory_percentiles.anon.d[01..12].csv`
 
 #### Schema
|Field|Description  |
|--|--|
| HashOwner | unique id of the application owner |
| HashApp | unique id for application name  |
|SampleCount | Number of samples used for computing the average |  
|AverageAllocatedMb | Average allocated memory across all SampleCount measurements throughout this 24h period<sup>8</sup> |  
|AverageAllocatedMb_pct1 | 1st percentile of the average allocated memory <sup>9</sup>|  
|AverageAllocatedMb_pct5 | 5th percentile of the average allocated memory <sup>9</sup>|  
|AverageAllocatedMb_pct25 | 25th percentile of the average allocated memory <sup>9</sup>|  
|AverageAllocatedMb_pct50 | 50th percentile of the average allocated memory <sup>9</sup>|  
|AverageAllocatedMb_pct75 | 75th percentile of the average allocated memory <sup>9</sup>|  
|AverageAllocatedMb_pct95 | 95th percentile of the average allocated memory <sup>9</sup>|  
|AverageAllocatedMb_pct99 | 99th percentile of the average allocated memory <sup>9</sup>|  
|AverageAllocatedMb_pct100 | 100th percentile of the average allocated memory <sup>9</sup>|

#### Notes
 8. Average allocated memory for the application (committed memory in Windows parlance): the total amount of virtual memory the process has allocated, not necessarily resident in physical memory. The framework samples the application memory every 5 seconds. Then, every minute, these samples are averaged. The average reported here is the average of all the 5-second samples for the application over all executions during the 24-h period. 
 9.  Like in the durations table, these percentiles are of the average, not of the true allocation. Under normal circumstances, averages are computed over 12 samples (taken every 5 seconds and aggregated every minute), except with workers start or end in a minute. We then take the weighted percentiles of these averages. For this dataset, there was a problem when logging the 0th-percentile, as under some edge cases, the value was erroneously recorded as 0, and we had to omit this value.

