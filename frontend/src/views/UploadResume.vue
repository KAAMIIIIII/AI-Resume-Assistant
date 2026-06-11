<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useResumeStore } from '@/stores/resume'
import { ElMessage } from 'element-plus'

const router = useRouter()
const resumeStore = useResumeStore()

const title = ref('')
const fileList = ref<any[]>([])
const uploading = ref(false)
const uploadRef = ref()

// Element Plus Upload 上传前校验：仅 PDF，不超过 10MB
const beforeUpload = (file: File) => {
  const isPDF = file.type === 'application/pdf'
  if (!isPDF) {
    ElMessage.error('仅支持 PDF 文件')
  }
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB')
  }
  return isPDF && isLt10M
}

const handleExceed = () => {
  ElMessage.warning('每次仅支持上传一份简历，如需更换请先删除当前文件')
}

async function handleUpload() {
  if (!title.value.trim()) {
    ElMessage.warning('请输入简历名称')
    return
  }
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择 PDF 文件')
    return
  }

  uploading.value = true
  try {
    // el-upload 中 auto-upload=false，手动取 raw 文件对象
    const file = fileList.value[0].raw
    const resume = await resumeStore.uploadResume(title.value, file)
    ElMessage.success('简历上传成功')

    // 上传完成后直接跳转到分析页面，引导用户输入 JD
    router.push(`/analysis/${resume.id}`)
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <div class="upload-card">
      <h2 class="card-title">上传简历</h2>
      <p class="card-desc">上传 PDF 格式的简历文件，AI 将自动解析并提供优化建议</p>

      <el-form label-position="top" class="upload-form">
        <el-form-item label="简历名称">
          <el-input
            v-model="title"
            placeholder="例如：张三-前端开发"
            size="large"
            maxlength="15"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="PDF 简历文件">
          <el-upload
            ref="uploadRef"
            v-model:file-list="fileList"
            :before-upload="beforeUpload"
            :on-exceed="handleExceed"
            :auto-upload="false"
            :limit="1"
            drag
            accept=".pdf"
          >
            <div class="upload-placeholder">
              <span class="upload-icon">📄</span>
              <p>将 PDF 文件拖到此处，或点击选择</p>
              <p class="upload-hint">仅支持 PDF 格式，大小不超过 10MB</p>
            </div>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" :loading="uploading" @click="handleUpload">
            上传并分析
          </el-button>
          <el-button size="large" @click="router.push('/')">取消</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.upload-card {
  max-width: 680px;
  margin: 0 auto;
  background: #fff;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.card-desc {
  color: #888;
  margin-bottom: 24px;
}

.upload-form {
  margin-top: 8px;
}

.upload-placeholder {
  text-align: center;
  padding: 40px 0;
}

.upload-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 12px;
}

.upload-hint {
  color: #bbb;
  font-size: 13px;
  margin-top: 8px;
}
</style>
