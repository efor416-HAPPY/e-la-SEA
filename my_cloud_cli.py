import sys
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError

class CloudServiceManager:
    """Base class for GCP Service Managers, enabling easy expansion to other services (Compute, BigQuery, etc.)."""
    def __init__(self, project_id):
        self.project_id = project_id

class GoogleCloudStorageManager(CloudServiceManager):
    """Object-Oriented Manager encapsulating Google Cloud Storage operations."""
    
    def __init__(self, project_id):
        super().__init__(project_id)
        # Automatically loads GCP credentials from environment variables (e.g., GOOGLE_APPLICATION_CREDENTIALS)
        self.client = storage.Client(project=self.project_id)

    def list_buckets(self):
        """Retrieves and displays all storage buckets within the project."""
        try:
            buckets = list(self.client.list_buckets())
            print(f"\n📦 [{self.project_id}] 프로젝트의 버킷 목록:")
            print("-" * 40)
            if not buckets:
                print("   (조회된 버킷이 없습니다)")
            for bucket in buckets:
                print(f"  - {bucket.name}")
            print("-" * 40)
        except GoogleAPIError as e:
            print(f"❌ GCS API 호출 중 오류가 발생했습니다: {e}")
        except Exception as e:
            print(f"❌ 예기치 못한 일반 오류가 발생했습니다: {e}")

    def create_bucket(self, bucket_name, location="asia-northeast3"):
        """Creates a new GCS bucket in the designated location (default: Seoul, South Korea)."""
        try:
            bucket = self.client.bucket(bucket_name)
            bucket.storage_class = "STANDARD"
            
            # Create the bucket in the specified GCP location
            new_bucket = self.client.create_bucket(bucket, location=location)
            print(f"✅ 버킷 '{new_bucket.name}'이(가) 지역 '{location}'에 성공적으로 생성되었습니다.")
        except GoogleAPIError as e:
            print(f"❌ 버킷 생성 중 API 오류가 발생했습니다: {e}")
        except Exception as e:
            print(f"❌ 예기치 못한 일반 오류가 발생했습니다: {e}")

class CloudCLIDispatcher:
    """Object-Oriented CLI dispatcher to parse positional arguments and run actions."""
    
    def __init__(self, argv):
        self.argv = argv

    def print_usage(self):
        print("\n💡 [OOP GCP Storage CLI]")
        print("사용법: python my_cloud_cli.py <프로젝트_ID> <명령어: list | create> [버킷_이름]")
        print("  예시 1 (조회): python my_cloud_cli.py my-gcp-project list")
        print("  예시 2 (생성): python my_cloud_cli.py my-gcp-project create my-new-unique-bucket-name\n")

    def run(self):
        if len(self.argv) < 3:
            self.print_usage()
            sys.exit(1)

        project_id = self.argv[1]
        command = self.argv[2]

        # Instantiate GCS Manager using OOP design
        storage_manager = GoogleCloudStorageManager(project_id)

        if command == "list":
            storage_manager.list_buckets()
        elif command == "create":
            if len(self.argv) < 4:
                print("❌ 버킷 생성시 생성할 버킷의 명칭을 입력해야 합니다.")
                sys.exit(1)
            bucket_name = self.argv[3]
            storage_manager.create_bucket(bucket_name)
        else:
            print(f"❌ 지원하지 않는 명령어입니다: '{command}'. ('list' 또는 'create'를 입력하세요)")
            self.print_usage()
            sys.exit(1)

if __name__ == "__main__":
    # Ensure console output supports Unicode (Korean & Emojis) on Windows terminals
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    dispatcher = CloudCLIDispatcher(sys.argv)
    dispatcher.run()
