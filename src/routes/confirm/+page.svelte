<script lang="ts">
    interface PageData {
        success: boolean;
        alreadyConfirmed: boolean;
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
                    class="mx-auto h-12 w-12 text-green-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M5 13l4 4L19 7"
                    />
                </svg>
                <h2
                    class="mt-6 text-center text-3xl font-extrabold text-gray-900"
                >
                    {#if data.alreadyConfirmed}
                        Already Confirmed!
                    {:else}
                        Subscription Confirmed!
                    {/if}
                </h2>
                <p class="mt-2 text-center text-sm text-gray-600">
                    You're all set. You will now receive high-signal market
                    impact alerts.
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
        {:else}
            <!-- Error state handled by SvelteKit error boundary -->
        {/if}
    </div>
</div>
