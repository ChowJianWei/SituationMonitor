<script lang="ts">
    interface PageData {
        success: boolean;
        alreadyUnsubscribed: boolean;
    }
    let { data }: { data: PageData } = $props();
</script>

<div
    class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8 items-center"
>
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
        {#if data.success}
            <div
                class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10 text-center"
            >
                <svg
                    class="mx-auto h-12 w-12 text-gray-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                </svg>
                <h2
                    class="mt-6 text-center text-3xl font-extrabold text-gray-900"
                >
                    {#if data.alreadyUnsubscribed}
                        Already Unsubscribed
                    {:else}
                        Unsubscribed Successfully
                    {/if}
                </h2>
                <p class="mt-2 text-center text-sm text-gray-600">
                    You will no longer receive alerts from Situation Monitor.
                </p>
                <div class="mt-6">
                    <a
                        href="/"
                        class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                        Back to Dashboard
                    </a>
                </div>
            </div>
        {/if}
    </div>
</div>
