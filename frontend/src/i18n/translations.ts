export type Language = 'en' | 'id';

export interface Translations {
  nav: {
    validations: string;
    lineage: string;
    impact: string;
    pipelines: string;
    investigation: string;
    recovery: string;
  };
  header: {
    subtitle: string;
    datasets: string;
    upload: string;
    scenario: string;
    compute: string;
    quality: string;
    guide: string;
  };
  scenario: {
    defective: string;
    corrected: string;
    load: string;
    loading: string;
    unload: string;
    unloading: string;
  };
  welcome: {
    title: string;
    subtitle: string;
    datasetOptionsHeading: string;
    reservedOptionTitle: string;
    reservedOptionDesc: string;
    customOptionTitle: string;
    customOptionDesc: string;
    whatIsHeading: string;
    whatIsDescription: string;
    whatIsPoints: {
      title: string;
      desc: string;
    }[];
    howWorksHeading: string;
    howWorksDescription: string;
    steps: {
      step: string;
      title: string;
      desc: string;
    }[];
    cta: string;
  };
  guide: {
    heading: string;
    subtitle: string;
    steps: {
      number: string;
      title: string;
      desc: string;
      actionTip?: string;
    }[];
    close: string;
  };
}

export const translations: Record<Language, Translations> = {
  en: {
    nav: {
      validations: 'Validations',
      lineage: 'Lineage',
      impact: 'Impact Analysis',
      pipelines: 'Pipelines',
      investigation: 'Investigation',
      recovery: 'Recovery',
    },
    header: {
      subtitle: 'Data Observability Platform',
      datasets: 'Datasets',
      upload: 'Upload',
      scenario: 'scenario:',
      compute: 'Compute:',
      quality: 'Quality:',
      guide: 'Guide',
    },
    scenario: {
      defective: 'Defective',
      corrected: 'Corrected',
      load: 'Load Scenario',
      loading: 'Loading Fixtures...',
      unload: 'Unload Scenario',
      unloading: 'Unloading...',
    },
    welcome: {
      title: 'Welcome to Lux',
      subtitle: 'Engineering-Grade Data Observability & Pipeline Integrity Platform',
      datasetOptionsHeading: 'Flexible Datasets: Use Reserved Scenario or Add Your Own',
      reservedOptionTitle: 'Option A: Reserved "Monday Revenue Mystery" Dataset',
      reservedOptionDesc:
        'Explore a pre-configured production pipeline incident out-of-the-box. Includes orders, order items, products, and inventory with switchable defective vs. clean fixtures and full DAG lineage—no setup required.',
      customOptionTitle: 'Option B: Add Your Own Custom Dataset',
      customOptionDesc:
        'Want to validate your own data? Click the "Upload" button at the top anytime to ingest custom CSV or JSON files, inspect inferred schemas, and execute deterministic quality rules against your datasets.',
      whatIsHeading: 'What is Lux?',
      whatIsDescription:
        'Lux is a specialized data observability platform built to solve the silent data corruption crisis. In modern data systems, scheduled ETL pipelines often complete with compute exit code 0 (SUCCESS), while secretly generating duplicate keys, corrupted totals, or orphan records that pollute executive dashboards and analytics.',
      whatIsPoints: [
        {
          title: 'Deterministic Quality Engine',
          desc: 'Evaluates structural, uniqueness, referential integrity, range, and temporal freshness rules against active datasets.',
        },
        {
          title: 'Dependency Lineage Graph (DAG)',
          desc: 'Traverses directed dependencies from source CSV files through transformations down to derived models, metrics, and BI reports.',
        },
        {
          title: 'Downstream Blast Radius Analysis',
          desc: 'Quantifies exact ripple effects and identifies affected consumer models before data reaches decision-makers.',
        },
        {
          title: 'Dual-Dimension Observability',
          desc: 'Disentangles compute execution health from data quality health to pinpoint silent anomalies.',
        },
        {
          title: 'Root Cause Investigations & Recovery',
          desc: 'Synthesizes validation findings into evidence-based diagnoses and verifies 100% recovery post-fix.',
        },
      ],
      howWorksHeading: 'How It Works',
      howWorksDescription:
        'Follow the guided observability journey across six dedicated workspaces:',
      steps: [
        {
          step: '01',
          title: 'Choose Dataset & Scenario',
          desc: 'Use our reserved "Monday Revenue Mystery" scenario (Defective or Corrected) OR upload your own CSV/JSON files using the "Upload" button.',
        },
        {
          step: '02',
          title: 'Execute Quality Validations',
          desc: 'Run deterministic rule checks to catch duplicate orders, negative inventory, and orphan items.',
        },
        {
          step: '03',
          title: 'Trace Lineage & Blast Radius',
          desc: 'Inspect DAG dependencies and quantify which downstream tables and executive reports are contaminated.',
        },
        {
          step: '04',
          title: 'Inspect Pipelines & Dual Status',
          desc: 'Observe the silent failure anomaly where compute jobs succeeded while data quality degraded.',
        },
        {
          step: '05',
          title: 'Investigate Root Cause',
          desc: 'Synthesize automated findings into an actionable incident diagnosis and generate exportable reports.',
        },
        {
          step: '06',
          title: 'Verify Clean Recovery',
          desc: 'Swap to Corrected fixtures and verify all validation rules turn green with zero residual violations.',
        },
      ],
      cta: 'Have fun',
    },
    guide: {
      heading: 'How this works',
      subtitle: 'A step-by-step walkthrough of the Lux observability workflow',
      steps: [
        {
          number: '1',
          title: 'Step 1: Choose Your Dataset (Reserved or Custom)',
          desc: 'You can work with our reserved signature dataset or add your own:\n• Reserved Dataset: Select "Monday Revenue Mystery" in the Scenario Tools. Choose "Defective" to simulate an active outage, or "Corrected" to verify recovery. Click "Load Scenario".\n• Your Own Dataset: Click the "Upload" button at the top to ingest your custom CSV or JSON files anytime.',
          actionTip: 'Tip: You can inspect loaded files anytime by clicking the "Datasets" button in the command bar.',
        },
        {
          number: '2',
          title: 'Step 2: Run Validations',
          desc: 'Open the Validations workspace and click "Execute Quality Validations". Lux evaluates structural, uniqueness, referential integrity, range, and temporal rules against active datasets. Click any finding row to open the Evidence Drawer and inspect violating rows.',
          actionTip: 'Filter by CRITICAL or HIGH severity to isolate primary blockers.',
        },
        {
          number: '3',
          title: 'Step 3: Explore Lineage DAG',
          desc: 'Navigate to the Lineage tab to visualize the full directed acyclic graph. Click any node to inspect upstream sources, downstream dependents, schemas, and metadata. Highlighted paths show how data flows from ingestion to executive reports.',
          actionTip: 'Use search and asset filters (Source, Transform, Derived, Metric, Report) to navigate complex graphs.',
        },
        {
          number: '4',
          title: 'Step 4: Analyze Blast Radius',
          desc: 'In the Impact Analysis tab, select a root dataset or transformation. Lux automatically traverses all downstream dependency edges, categorizes assets as DIRECT or TRANSITIVE consumers, and tallies the total affected blast radius.',
          actionTip: 'Trace from "orders.csv" to see how dirty orders cascade to the executive dashboard.',
        },
        {
          number: '5',
          title: 'Step 5: Monitor Pipeline Observability',
          desc: 'In the Pipelines tab, review historical orchestration runs and partition freshness. Notice the critical Dual-Status insight: compute return codes were 0 (SUCCESS), yet data quality was CORRUPTED.',
          actionTip: 'Check partition freshness SLA to spot delayed or lagging pipelines.',
        },
        {
          number: '6',
          title: 'Step 6: Review Incident Investigation',
          desc: 'The Investigation tab synthesizes validated telemetry into structured facts, confirmed hypotheses, and prioritized action items. Generate comprehensive HTML or JSON incident reports for stakeholder post-mortems.',
          actionTip: 'Click "Export HTML" to download a clean, standalone incident summary.',
        },
        {
          number: '7',
          title: 'Step 7: Verify Recovery',
          desc: 'In the Recovery tab, click "Verify Recovery". Lux swaps active files to corrected fixtures, re-runs all validation rules, recalculates downstream lineage health, and provides mathematical verification that 100% of findings are resolved.',
          actionTip: 'All 8 quality rules should pass with green checkmarks upon recovery.',
        },
      ],
      close: 'Close guide',
    },
  },
  id: {
    nav: {
      validations: 'Validasi',
      lineage: 'Silsilah Lineage',
      impact: 'Analisis Dampak',
      pipelines: 'Riwayat Pipeline',
      investigation: 'Investigasi',
      recovery: 'Pemulihan',
    },
    header: {
      subtitle: 'Data Observability Platform',
      datasets: 'Dataset',
      upload: 'Unggah',
      scenario: 'skenario:',
      compute: 'Komputasi:',
      quality: 'Kualitas:',
      guide: 'Panduan',
    },
    scenario: {
      defective: 'Rusak (Defective)',
      corrected: 'Bersih (Corrected)',
      load: 'Muat Skenario',
      loading: 'Memuat Data...',
      unload: 'Bongkar Skenario',
      unloading: 'Membongkar...',
    },
    welcome: {
      title: 'Selamat Datang di Lux',
      subtitle: 'Platform Observabilitas Data & Integritas Pipeline Tingkat Rekayasa',
      datasetOptionsHeading: 'Pilihan Dataset Fleksibel: Gunakan Skenario Bawaan atau Tambahkan Data Anda Sendiri',
      reservedOptionTitle: 'Opsi A: Dataset Khusus Bawaan "Monday Revenue Mystery"',
      reservedOptionDesc:
        'Eksplorasi simulasi insiden pipeline e-commerce siap pakai. Sudah mencakup data orders, order items, products, dan inventory dengan opsi data rusak (Defective) vs. data bersih (Corrected) beserta graf silsilah DAG lengkap—tanpa perlu persiapan file apa pun.',
      customOptionTitle: 'Opsi B: Tambahkan Dataset Anda Sendiri',
      customOptionDesc:
        'Ingin memvalidasi data Anda sendiri? Klik tombol "Upload" (Unggah) di bagian atas kapan saja untuk mengunggah file CSV atau JSON milik Anda, memeriksa skema, dan mengeksekusi aturan validasi kualitas data secara deterministik.',
      whatIsHeading: 'Apa itu Lux?',
      whatIsDescription:
        'Lux adalah platform observabilitas data khusus yang dirancang untuk mengatasi krisis kerusakan data tersembunyi (silent data corruption). Pada sistem data modern, proses ETL terjadwal kerap kali selesai dengan status sukses (SUCCESS / exit code 0), namun diam-diam memproduksi kunci duplikat, rekaman yatim (orphan rows), atau data rusak yang mengotori dasbor analitik dan laporan eksekutif.',
      whatIsPoints: [
        {
          title: 'Mesin Validasi Deterministik',
          desc: 'Mengevaluasi keunikan, integritas referensial, struktur skema, rentang nilai, dan kesegaran temporal terhadap dataset aktif.',
        },
        {
          title: 'Graf Silsilah Dependensi (DAG)',
          desc: 'Menelusuri relasi berarah dari file sumber mentah CSV melewati transformasi data hingga tabel turunan, metrik bisnis, dan laporan BI.',
        },
        {
          title: 'Analisis Radius Dampak (Blast Radius)',
          desc: 'Mengukur dampak riak dan mengisolasi model konsumen hilir yang terancam sebelum data sampai ke pengambil keputusan.',
        },
        {
          title: 'Observabilitas Dual-Status',
          desc: 'Memisahkan kesehatan proses komputasi dari kesehatan kualitas data sebenarnya untuk menemukan anomali tersembunyi.',
        },
        {
          title: 'Investigasi Akar Masalah & Pemulihan',
          desc: 'Menyintesis temuan validasi menjadi diagnosis berbasis bukti otentik serta memverifikasi pemulihan data 100% pasca-perbaikan.',
        },
      ],
      howWorksHeading: 'Cara Kerja Platform',
      howWorksDescription:
        'Ikuti alur observabilitas terpandu melalui enam ruang kerja terintegrasi:',
      steps: [
        {
          step: '01',
          title: 'Pilih Sumber Data & Skenario',
          desc: 'Gunakan dataset bawaan kami "Monday Revenue Mystery" (Defective atau Corrected) ATAU unggah file CSV/JSON Anda sendiri lewat tombol "Upload".',
        },
        {
          step: '02',
          title: 'Jalankan Validasi Kualitas',
          desc: 'Eksekusi aturan deterministik untuk mendeteksi pesanan duplikat, stok negatif, dan foreign key yang tidak cocok.',
        },
        {
          step: '03',
          title: 'Telusuri Lineage & Radius Dampak',
          desc: 'Periksa dependensi DAG dan tentukan tabel hilir mana saja yang terancam terkena dampak data rusak.',
        },
        {
          step: '04',
          title: 'Periksa Pipeline & Dual Status',
          desc: 'Amati anomali komputasi di mana proses ETL sukses (exit code 0), namun data yang dihasilkan rusak.',
        },
        {
          step: '05',
          title: 'Investigasi Akar Masalah',
          desc: 'Telaah diagnosis insiden berbasis bukti dan buat laporan komprehensif yang siap diunduh.',
        },
        {
          step: '06',
          title: 'Verifikasi Pemulihan Bersih',
          desc: 'Ganti ke data Corrected dan pastikan semua aturan validasi kembali hijau dengan 0 pelanggaran tersisa.',
        },
      ],
      cta: 'Selamat Menjelajah',
    },
    guide: {
      heading: 'How this works',
      subtitle: 'Panduan langkah demi langkah cara kerja alur observabilitas Lux',
      steps: [
        {
          number: '1',
          title: 'Langkah 1: Pilih Sumber Dataset (Data Bawaan atau Data Sendiri)',
          desc: 'Anda dapat memilih antara dua sumber data:\n• Dataset Bawaan: Pilih "Monday Revenue Mystery" pada Alat Skenario. Pilih "Defective" untuk simulasi insiden atau "Corrected" untuk menguji pemulihan, lalu klik "Muat Skenario".\n• Dataset Anda Sendiri: Klik tombol "Upload" di menu atas kapan saja untuk mengunggah file CSV atau JSON milik Anda.',
          actionTip: 'Tips: Anda dapat melihat seluruh dataset yang dimuat kapan saja dengan mengklik tombol "Datasets" di menu utama.',
        },
        {
          number: '2',
          title: 'Langkah 2: Jalankan Validasi',
          desc: 'Buka ruang kerja Validasi dan klik "Jalankan Validasi Kualitas". Lux mengevaluasi aturan struktural, keunikan, integritas referensial, dan rentang nilai. Klik baris temuan mana pun untuk membuka Laci Bukti dan memeriksa rekaman baris yang melanggar.',
          actionTip: 'Gunakan filter severitas CRITICAL atau HIGH untuk mengisolasi masalah utama.',
        },
        {
          number: '3',
          title: 'Langkah 3: Telusuri Graf Lineage',
          desc: 'Buka tab Lineage untuk melihat graf asiklik terarah (DAG) interaktif secara penuh. Klik node mana saja untuk memeriksa data hulu, konsumen hilir, skema, dan metadata. Garis yang tersorot menunjukkan aliran data hingga laporan eksekutif.',
          actionTip: 'Gunakan pencarian dan filter jenis aset (Source, Transform, Derived, Metric, Report) untuk navigasi cepat.',
        },
        {
          number: '4',
          title: 'Langkah 4: Analisis Radius Dampak',
          desc: 'Pada tab Impact Analysis, pilih dataset akar masalah. Lux otomatis menelusuri seluruh dependensi hilir, mengkategorikan aset sebagai konsumen langsung atau transitif, dan menghitung total radius dampak.',
          actionTip: 'Telusuri dari "orders.csv" untuk melihat bagaimana pesanan kotor merembet hingga dasbor eksekutif.',
        },
        {
          number: '5',
          title: 'Langkah 5: Pantau Observabilitas Pipeline',
          desc: 'Pada tab Pipelines, periksa riwayat eksekusi dan kesegaran partisi. Perhatikan wawasan Dual-Status penting: kode kembali komputasi bernilai 0 (SUCCESS), namun kesehatan data bernilai CORRUPTED.',
          actionTip: 'Periksa SLA kesegaran partisi untuk mengetahui apakah ada pipeline yang tertunda.',
        },
        {
          number: '6',
          title: 'Langkah 6: Telaah Investigasi Insiden',
          desc: 'Tab Investigasi merangkum telemetri tervalidasi menjadi fakta terstruktur, hipotesis terkonfirmasi, dan daftar tindakan perbaikan. Buat laporan insiden HTML atau JSON yang siap dibagikan untuk evaluasi tim.',
          actionTip: 'Klik "Ekspor HTML" untuk mengunduh ringkasan insiden mandiri yang rapi.',
        },
        {
          number: '7',
          title: 'Langkah 7: Verifikasi Pemulihan',
          desc: 'Pada tab Recovery, klik "Verifikasi Pemulihan". Lux mengganti file aktif ke dataset bersih, mengevaluasi ulang semua aturan validasi, memperbarui kesehatan silsilah hilir, dan membuktikan secara pasti bahwa 100% temuan telah pulih.',
          actionTip: 'Semua 8 aturan validasi kualitas data harus berstatus lolos (hijau) setelah pemulihan.',
        },
      ],
      close: 'Tutup Panduan',
    },
  },
};
