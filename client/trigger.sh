#!/bin/bash

# 设置任务创建接口和任务详情接口的 URL
BASE_URL=${BASE_URL:-"http://127.0.0.1:9001"}  # 修改为实际接口地址或使用环境变量
CREATE_TASK_ENDPOINT="$BASE_URL/task"
GET_TASK_ENDPOINT="$BASE_URL/task"

# 通过环境变量接收接口的三个参数
JOURNAL_NAME=${JOURNAL_NAME}
TASK_TYPE=${TASK_TYPE}
TASK_SETUP=${TASK_SETUP}

# 日志文件路径
LOG_FILE="task_log_$(date '+%Y%m%d_%H%M%S').log"

# 打印并记录日志的函数
log() {
  echo "$1" | tee -a "$LOG_FILE"
}

# 检查参数是否为空
if [[ -z "$JOURNAL_NAME" || -z "$TASK_TYPE" || -z "$TASK_SETUP" ]]; then
  log "Error: JOURNAL_NAME, TASK_TYPE, 和 TASK_SETUP 这三个参数必须全部提供。"
  log "当前参数值："
  log "JOURNAL_NAME: $JOURNAL_NAME"
  log "TASK_TYPE: $TASK_TYPE"
  log "TASK_SETUP: $TASK_SETUP"
  exit 1
fi

# 打印传入的参数
log "创建任务的参数:"
log "Journal Name: $JOURNAL_NAME"
log "Task Type: $TASK_TYPE"
log "Task Setup: $TASK_SETUP"
log "Base URL: $BASE_URL"

# 创建任务
log "执行命令: curl -s -X POST \"$CREATE_TASK_ENDPOINT\" -H \"Content-Type: application/json\" -d '{\"journal_name\":\"$JOURNAL_NAME\",\"type\":\"$TASK_TYPE\",\"task_setup\":$TASK_SETUP}'"
RESPONSE=$(curl -s -X POST "$CREATE_TASK_ENDPOINT" -H "Content-Type: application/json" -d "{\"journal_name\":\"$JOURNAL_NAME\",\"type\":\"$TASK_TYPE\",\"task_setup\":$TASK_SETUP}")

# 记录创建任务的响应
log "创建任务的响应数据: $RESPONSE"

# 检查创建任务的响应
CREATE_TASK_CODE=$(echo "$RESPONSE" | jq -r '.code')

if [[ "$CREATE_TASK_CODE" != "200" ]]; then
  log "创建任务失败，错误码: $CREATE_TASK_CODE"
  exit 1
fi

TASK_ID=$(echo "$RESPONSE" | jq -r '.data.id')

if [[ "$TASK_ID" == "null" || -z "$TASK_ID" ]]; then
  log "任务创建失败，无法获取任务ID"
  exit 1
fi

log "任务创建成功，任务ID: $TASK_ID"

# 轮询查询任务状态，直到任务完成
while true; do
  # 查询任务详情
#  log "执行命令: curl -s -X GET \"$GET_TASK_ENDPOINT?id=$TASK_ID\""
  TASK_RESPONSE=$(curl -s -X GET "$GET_TASK_ENDPOINT?id=$TASK_ID")

  # 记录查询任务的响应
#  log "查询任务详情的响应数据: $TASK_RESPONSE"

  # 解析任务状态和统计信息
  STATUS=$(echo "$TASK_RESPONSE" | jq -r '.status')
  SUCCESS_COUNT=$(echo "$TASK_RESPONSE" | jq -r '.success_count')
  FAIL_COUNT=$(echo "$TASK_RESPONSE" | jq -r '.failed_count')
  TOTAL_COUNT=$(echo "$TASK_RESPONSE" | jq -r '.total_count')

  # 输出已处理数/总数
  if [[ "$TOTAL_COUNT" != "null" && "$SUCCESS_COUNT" != "null" && "$FAIL_COUNT" != "null" ]]; then
    log "当前状态: $STATUS / 成功数：$SUCCESS_COUNT/ 失败数：$FAIL_COUNT / 总数: $TOTAL_COUNT"
  fi

  # 判断任务状态
  if [[ "$STATUS" == "finish" ]]; then
    log "任务完成"
    break
  elif [[ "$STATUS" == "failed" ]]; then
    FAILED_REASON=$(echo "$TASK_RESPONSE" | jq -r '.failed_reason')
    log "任务失败，失败原因：$FAILED_REASON"
    exit 1
  else
    log "任务未完成，当前状态: $STATUS，继续轮询..."
  fi

  # 等待 5 秒后再次查询
  sleep 5
done
# 定义最大宽度
MAX_WIDTH=70

# 提取任务详情字段
TASK_ID=$(echo "$TASK_RESPONSE" | jq -r '.id')
TASK_STATUS=$(echo "$TASK_RESPONSE" | jq -r '.status')
TASK_SUCCESS_COUNT=$(echo "$TASK_RESPONSE" | jq -r '.success_count')
TASK_FAIL_COUNT=$(echo "$TASK_RESPONSE" | jq -r '.failed_count')
TASK_TOTAL_COUNT=$(echo "$TASK_RESPONSE" | jq -r '.total_count')
TASK_JOURNAL_NAME=$(echo "$TASK_RESPONSE" | jq -r '.journal_name')
TASK_TYPE=$(echo "$TASK_RESPONSE" | jq -r '.type')
TASK_CREATE_TIME=$(echo "$TASK_RESPONSE" | jq -r '.create_time')
TASK_END_TIME=$(echo "$TASK_RESPONSE" | jq -r '.end_time')
TASK_PARENT_ID=$(echo "$TASK_RESPONSE" | jq -r '.parent_task_id')

# 提取 result_detail 中的列表
FAIL_LIST=$(echo "$TASK_RESPONSE" | jq -r '.result_detail.fail_list[]')
SUCCESS_LIST=$(echo "$TASK_RESPONSE" | jq -r '.result_detail.success_list[]')
TOTAL_LIST=$(echo "$TASK_RESPONSE" | jq -r '.result_detail.total_list[]')


# 输出任务详情表格
echo "任务ID：$TASK_ID"
echo "类型：$TASK_TYPE"
echo "数据源：$TASK_JOURNAL_NAME"
echo "状态：$TASK_STATUS" ""
echo "总数：$TASK_TOTAL_COUNT"
echo "成功数量：$TASK_SUCCESS_COUNT"
echo "失败数量：$TASK_FAIL_COUNT"
echo "创建时间：$TASK_CREATE_TIME"
echo "结束时间：$TASK_END_TIME"
log "+------------------+----------------------------------------------------------------------+"
echo "失败列表："
# 打印 result_detail 部分
for item in $FAIL_LIST; do
    echo "$item(失败)"
done

echo "成功列表："
for item in $SUCCESS_LIST; do
    echo "$item(成功)"
done
