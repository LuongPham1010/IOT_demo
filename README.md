# Demo Phát Hiện Xâm Nhập Mạng IoT

Dự án này là một kịch bản demo đơn giản để mô phỏng và phát hiện một cuộc tấn công từ chối dịch vụ (DoS) kiểu "flooding" trong một mạng IoT dựa trên giao thức MQTT.

## Tổng quan

Kịch bản bao gồm ba thành phần chính:

1.  **`benign_client.py`**: Một client MQTT mô phỏng một thiết bị IoT bình thường, gửi dữ liệu cảm biến định kỳ 5 giây một lần.
2.  **`attacker_client.py`**: Một client MQTT mô phỏng kẻ tấn công, liên tục gửi một lượng lớn tin nhắn đến broker để gây quá tải hệ thống.
3.  **`run_experiment.py`**: File điều phối chính, thực hiện các công việc sau:
    *   Chạy các client để tạo ra hai kịch bản mạng: bình thường và bị tấn công.
    *   Sử dụng `tshark` để bắt và ghi lại gói tin mạng trong cả hai kịch bản.
    *   Trích xuất các đặc trưng (features) từ dữ liệu mạng đã thu thập.
    *   Huấn luyện một mô hình học máy (`RandomForestClassifier`) để phân biệt giữa lưu lượng mạng bình thường và lưu lượng tấn công.
    *   Đánh giá hiệu suất của mô hình và trực quan hóa kết quả.

## Yêu cầu cài đặt

Dự án này yêu cầu cài đặt các thư viện Python và một số phần mềm hệ thống.

### 1. Thư viện Python

Cài đặt các thư viện Python cần thiết bằng file `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Phần mềm hệ thống

Bạn cần cài đặt TShark và một MQTT Broker (khuyến nghị Mosquitto).

#### Cài đặt TShark (Wireshark)

TShark là công cụ dòng lệnh của Wireshark. Cách dễ nhất để cài đặt nó là cài đặt Wireshark.

*   **Trên Windows:**
    1.  Tải bộ cài đặt từ [trang chủ Wireshark](https://www.wireshark.org/download.html).
    2.  Chạy file `.exe`. Trong quá trình cài đặt, **hãy chắc chắn rằng bạn đã tick vào ô "Add Wireshark to the system PATH"** để có thể gọi lệnh `tshark` từ Command Prompt hoặc PowerShell.

*   **Trên macOS (sử dụng [Homebrew](https://brew.sh/)):**
    ```bash
    brew install wireshark
    ```

*   **Trên Linux (Ubuntu/Debian):**
    ```bash
    sudo apt update
    sudo apt install tshark
    ```
    *   Trong quá trình cài đặt, một hộp thoại sẽ hiện lên hỏi `Should non-superusers be able to capture packets?`. Chọn **<Yes>** để tiện lợi hơn khi chạy script mà không cần `sudo`.

*   **Kiểm tra cài đặt:**
    Sau khi cài đặt xong, mở một terminal mới và chạy lệnh `tshark --version`. Nếu bạn thấy thông tin phiên bản hiện ra, nghĩa là cài đặt đã thành công.

#### Cài đặt MQTT Broker (Mosquitto)

*   **Trên Windows:**
    1.  Tải bộ cài đặt từ [trang chủ Mosquitto](https://mosquitto.org/download/).
    2.  Chạy file installer. Sau khi cài đặt, Mosquitto thường sẽ chạy như một dịch vụ (service) nền.

*   **Trên macOS (sử dụng Homebrew):**
    ```bash
    brew install mosquitto
    ```
    *   Để khởi động broker và cho nó chạy nền, dùng lệnh:
        ```bash
        brew services start mosquitto
        ```

*   **Trên Linux (Ubuntu/Debian):**
    ```bash
    sudo apt update
    sudo apt install mosquitto mosquitto-clients
    ```
    *   Dịch vụ Mosquitto sẽ tự động khởi động sau khi cài đặt. Bạn có thể kiểm tra trạng thái bằng lệnh:
        ```bash
        sudo systemctl status mosquitto
        ```

*   **Kiểm tra Broker:**
    Broker sẽ lắng nghe trên cổng `1883`. Script sẽ tự động kết nối đến `localhost:1883`.

## Hướng dẫn chạy thực nghiệm

### Bước 1: Khởi động MQTT Broker

Đảm bảo rằng MQTT broker (ví dụ: Mosquitto) của bạn đang chạy và lắng nghe trên cổng `1883`.

### Bước 2: Chạy kịch bản

Chạy kịch bản từ terminal bằng lệnh `python run_experiment.py`. Script hỗ trợ các đối số dòng lệnh để tùy chỉnh hoạt động.

Để xem tất cả các tùy chọn, hãy chạy:
```bash
python run_experiment.py --help
```

**Ví dụ sử dụng:**

1.  **Chạy với cài đặt mặc định:**
    (Sử dụng interface `lo`, thu thập trong `120` giây cho mỗi kịch bản)
    ```bash
    python run_experiment.py
    ```

2.  **Chỉ định interface mạng:**
    Nếu `tshark -D` cho thấy interface của bạn là `lo0` (phổ biến trên macOS), hãy sử dụng tùy chọn `-i` hoặc `--interface`.
    ```bash
    python run_experiment.py --interface lo0
    ```

3.  **Thay đổi thời gian thu thập dữ liệu:**
    Để thu thập dữ liệu trong `30` giây cho mỗi kịch bản, sử dụng tùy chọn `-t` hoặc `--time`.
    ```bash
    python run_experiment.py -t 30
    ```

4.  **Kết hợp các tùy chọn:**
    ```bash
    python run_experiment.py -i eth0 -t 120 --normal-out normal_traffic.pcap --attack-out attack_traffic.pcap
    ```

Tập lệnh sẽ tự động thực hiện các bước sau:
1.  Thu thập 120 giây (mặc định) dữ liệu cho lưu lượng bình thường và lưu vào `normal.pcap`.
2.  Thu thập 120 giây (mặc định) dữ liệu cho lưu lượng tấn công và lưu vào `attack.pcap`.
3.  Trích xuất đặc trưng, huấn luyện mô hình, và in ra báo cáo phân loại (classification report).
4.  Hiển thị ma trận nhầm lẫn (confusion matrix) dưới dạng một biểu đồ.

## Kết quả mong đợi

Sau khi chạy xong, bạn sẽ thấy:
*   Các thông báo trạng thái trong terminal về quá trình thu thập dữ liệu và huấn luyện mô hình.
*   Một báo cáo phân loại (classification report) cho thấy độ chính xác, precision, recall của mô hình.
*   Một cửa sổ biểu đồ hiển thị ma trận nhầm lẫn, giúp bạn đánh giá trực quan hiệu suất của mô hình trong việc phân loại hai loại lưu lượng.
